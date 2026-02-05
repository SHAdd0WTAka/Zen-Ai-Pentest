"""
VPN Management Endpoints

Control Proton VPN integration for secure anonymous scanning.
"""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from api.core.auth import get_current_user
from api.models.user import User
from modules.protonvpn import ProtonVPNManager, VPNProtocol, VPNSecurityLevel

router = APIRouter()
vpn_manager = ProtonVPNManager()


class VPNStatusResponse(BaseModel):
    """VPN connection status"""

    connected: bool
    server_ip: Optional[str]
    server_location: Optional[str]
    protocol: Optional[str]
    public_ip: Optional[str]
    original_ip: Optional[str]
    connection_time: Optional[str]
    kill_switch: bool


class VPNConnectRequest(BaseModel):
    """VPN connection request"""

    country: str = Field(
        default="CH", description="ISO country code (CH, NL, SE, etc.)"
    )
    protocol: VPNProtocol = Field(default=VPNProtocol.WIREGUARD)
    security_level: VPNSecurityLevel = Field(default=VPNSecurityLevel.STANDARD)
    p2p: bool = Field(default=False)
    kill_switch: bool = Field(default=True)


class ServerInfo(BaseModel):
    """VPN server information"""

    name: str
    country: str
    city: Optional[str]
    load: int
    features: List[str]


@router.get("/status", response_model=VPNStatusResponse)
async def get_vpn_status(current_user: User = Depends(get_current_user)):
    """Get current VPN connection status"""
    status = vpn_manager.get_status()
    return status.to_dict()


@router.post("/connect", response_model=VPNStatusResponse)
async def connect_vpn(
    request: VPNConnectRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Connect to Proton VPN.

    - **country**: Target country code (CH=Swiss, NL=Netherlands, etc.)
    - **protocol**: WireGuard (fast), OpenVPN-TCP/UDP
    - **security_level**: Standard, Secure-Core (multi-hop), Tor, P2P
    - **kill_switch**: Prevent IP leaks if VPN disconnects
    """
    try:
        status = await vpn_manager.connect(
            country=request.country,
            protocol=request.protocol,
            security_level=request.security_level,
            p2p=request.p2p,
            kill_switch=request.kill_switch,
        )
        return status.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VPN connection failed: {str(e)}")


@router.post("/disconnect", response_model=VPNStatusResponse)
async def disconnect_vpn(current_user: User = Depends(get_current_user)):
    """Disconnect from VPN"""
    try:
        status = await vpn_manager.disconnect()
        return status.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VPN disconnect failed: {str(e)}")


@router.post("/rotate")
async def rotate_vpn_ip(
    country: Optional[str] = None, current_user: User = Depends(get_current_user)
):
    """Rotate VPN IP address (disconnect and reconnect)"""
    try:
        status = await vpn_manager.rotate_ip(country=country)
        return {"message": "IP rotated successfully", "status": status.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IP rotation failed: {str(e)}")


@router.get("/servers", response_model=List[ServerInfo])
async def list_servers(
    country: Optional[str] = None, current_user: User = Depends(get_current_user)
):
    """List available VPN servers"""
    servers = await vpn_manager.get_server_list(country=country)
    return [
        {
            "name": s.name,
            "country": s.country,
            "city": s.city,
            "load": s.load,
            "features": s.features,
        }
        for s in servers
    ]


@router.get("/servers/recommended")
async def get_recommended_server(
    purpose: str = "general", current_user: User = Depends(get_current_user)
):
    """
    Get recommended server for specific purpose.

    - **purpose**: general, pentest, c2, fileshare
    """
    require_p2p = purpose == "fileshare"
    require_secure_core = purpose == "pentest"

    server = await vpn_manager.recommend_server(
        purpose=purpose,
        require_p2p=require_p2p,
        require_secure_core=require_secure_core,
    )

    if not server:
        raise HTTPException(status_code=404, detail="No suitable server found")

    return {
        "recommended": {
            "name": server.name,
            "country": server.country,
            "city": server.city,
            "load": server.load,
            "features": server.features,
        },
        "purpose": purpose,
    }


@router.get("/leak-test")
async def test_vpn_leaks(current_user: User = Depends(get_current_user)):
    """Test for IP/DNS/WebRTC leaks"""
    results = vpn_manager.check_ip_leak()
    return results


@router.get("/history")
async def get_connection_history(
    limit: int = 50, current_user: User = Depends(get_current_user)
):
    """Get VPN connection history"""
    history = vpn_manager.get_connection_history()
    return {"history": history[-limit:]}


@router.post("/check-ip")
async def check_public_ip(current_user: User = Depends(get_current_user)):
    """Check current public IP address"""
    ip = await vpn_manager.get_public_ip()
    return {"public_ip": ip, "vpn_connected": vpn_manager.is_connected()}
