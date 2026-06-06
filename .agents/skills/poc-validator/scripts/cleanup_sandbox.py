#!/usr/bin/env python3
"""
Sandbox Cleanup Utility

Cleans up Docker containers, temporary files, and resources
after PoC validation execution.
"""

import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("sandbox_cleanup")


async def cleanup_container(container_id: str, force: bool = False) -> bool:
    """
    Clean up a specific container.

    Args:
        container_id: Docker container ID or name
        force: Force kill before removal
    """
    try:
        if force:
            process = await asyncio.create_subprocess_exec(
                "docker", "kill", container_id, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.wait_for(process.wait(), timeout=5)

        process = await asyncio.create_subprocess_exec(
            "docker", "rm", "-f", container_id, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.wait_for(process.wait(), timeout=10)

        logger.info(f"Cleaned up container: {container_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to cleanup container {container_id}: {e}")
        return False


async def cleanup_all_sandboxes(prefix: str = "zen-sandbox-") -> dict:
    """
    Clean up all sandbox containers matching prefix.

    Args:
        prefix: Container name prefix to match

    Returns:
        Dict with cleanup statistics
    """
    stats = {"found": 0, "removed": 0, "failed": 0}

    try:
        # List containers
        process = await asyncio.create_subprocess_exec(
            "docker", "ps", "-aq", "--filter", f"name={prefix}", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()

        container_ids = stdout.decode().strip().split("\n")
        container_ids = [c for c in container_ids if c]

        stats["found"] = len(container_ids)

        # Remove each container
        for container_id in container_ids:
            if await cleanup_container(container_id, force=True):
                stats["removed"] += 1
            else:
                stats["failed"] += 1

        logger.info(f"Sandbox cleanup complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Sandbox cleanup failed: {e}")
        return stats


async def cleanup_old_containers(max_age_hours: int = 24) -> dict:
    """
    Remove containers older than specified hours.

    Args:
        max_age_hours: Maximum age in hours
    """
    stats = {"found": 0, "removed": 0}

    try:
        # Get all containers with creation time
        process = await asyncio.create_subprocess_exec(
            "docker",
            "ps",
            "-aq",
            "--format",
            "{{.ID}}|{{.CreatedAt}}|{{.Names}}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()

        cutoff = datetime.now() - timedelta(hours=max_age_hours)

        for line in stdout.decode().strip().split("\n"):
            if not line:
                continue

            parts = line.split("|")
            if len(parts) >= 2:
                container_id = parts[0]
                created_str = parts[1]
                name = parts[2] if len(parts) > 2 else "unknown"

                # Parse creation time (Docker format: 2026-03-20 14:30:00 +0000 UTC)
                try:
                    created = datetime.strptime(created_str[:19], "%Y-%m-%d %H:%M:%S")

                    if created < cutoff and "zen-sandbox" in name:
                        stats["found"] += 1
                        if await cleanup_container(container_id):
                            stats["removed"] += 1

                except ValueError:
                    continue

        return stats

    except Exception as e:
        logger.error(f"Old container cleanup failed: {e}")
        return stats


async def prune_docker_system() -> dict:
    """
    Prune unused Docker resources.

    WARNING: This affects all Docker resources, not just sandbox.
    """
    stats = {}

    try:
        # Prune containers
        process = await asyncio.create_subprocess_exec(
            "docker", "container", "prune", "-f", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        stats["containers"] = stdout.decode().strip()

        # Prune networks
        process = await asyncio.create_subprocess_exec(
            "docker", "network", "prune", "-f", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        stats["networks"] = stdout.decode().strip()

        # Prune volumes (be careful!)
        # process = await asyncio.create_subprocess_exec(
        #     "docker", "volume", "prune", "-f",
        #     stdout=asyncio.subprocess.PIPE,
        #     stderr=asyncio.subprocess.PIPE
        # )

        return stats

    except Exception as e:
        logger.error(f"Docker prune failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) > 1 and sys.argv[1] == "--all":
            # Full cleanup
            print("Cleaning up all sandbox containers...")
            result = await cleanup_all_sandboxes()
            print(f"Removed {result['removed']} of {result['found']} containers")

            print("\nCleaning up old containers...")
            old = await cleanup_old_containers(max_age_hours=1)
            print(f"Removed {old['removed']} old containers")

        elif len(sys.argv) > 1:
            # Cleanup specific container
            container_id = sys.argv[1]
            print(f"Cleaning up container: {container_id}")
            success = await cleanup_container(container_id, force=True)
            print(f"Success: {success}")

        else:
            print("Usage:")
            print("  python cleanup_sandbox.py <container_id>")
            print("  python cleanup_sandbox.py --all")

    asyncio.run(main())
