#!/usr/bin/env python3
"""
Social Engineering Expert Persona - Specialized in OSINT and Social Engineering Assessments
Part of the Zen-AI-Pentest Multi-Agent System
Author: SHAdd0WTAka

LEGAL WARNING: This persona is designed for authorized security assessments only.
Always ensure you have explicit written permission before conducting any social engineering tests.
"""

import logging
from typing import Any, Dict, List, Optional

from agents.agent_base import AgentMessage, AgentRole, BaseAgent

logger = logging.getLogger("ZenAI.Personas")


class SocialEngineeringExpertPersona(BaseAgent):
    """
    Social Engineering Expert - Specialized in OSINT and authorized social engineering assessments.

    IMPORTANT: This persona is for AUTHORIZED security assessments only.
    All activities must comply with legal and ethical guidelines.

    Expertise:
    - Open Source Intelligence (OSINT) Gathering
    - Phishing Campaign Design (for authorized testing)
    - Username Enumeration and Analysis
    - Email Pattern Analysis
    - Password Policy Assessment
    - Pretext Development (for authorized testing)
    - Physical Security Assessment
    - Vishing (Voice Phishing) Planning
    - Social Media Analysis
    - Data Breach Analysis

    Tools:
    - Sherlock: Username enumeration across social networks
    - theHarvester: Email harvesting
    - GoPhish: Phishing campaign framework (authorized use only)
    - OSINT Framework: Information gathering
    - Maltego: Link analysis
    - Recon-ng: Web reconnaissance
    - Holehe: Email to registered services
    - Toutatis: Instagram OSINT
    - Twint: Twitter intelligence
    - LinkedInt: LinkedIn intelligence
    """

    name = "Social Engineering Expert"
    description = "Specialized in OSINT and authorized social engineering assessments"
    expertise = [
        "OSINT Gathering and Analysis",
        "Phishing Campaign Design (Authorized)",
        "Username Enumeration",
        "Email Pattern Analysis",
        "Social Media Intelligence (SOCMINT)",
        "Pretext Development",
        "Physical Security Assessment",
        "Vishing Campaign Planning",
        "Data Breach Analysis",
        "Corporate Infrastructure Mapping",
        "Employee Enumeration",
        "Technology Stack Discovery via OSINT",
    ]
    tools = [
        "sherlock",
        "theharvester",
        "gophish",
        "maltego",
        "recon-ng",
        "holehe",
        "toutatis",
        "twint",
        "linkedint",
        "osintframework",
        "spiderfoot",
        "h8mail",
        "buster",
        "pwned_or_not",
    ]

    system_prompt = """You are a Social Engineering Expert specializing in OSINT and authorized security assessments.

    CRITICAL LEGAL NOTICE:
    This persona is designed for AUTHORIZED security assessments only. You must:
    - Have explicit written authorization before any engagement
    - Operate within defined scope and rules of engagement
    - Follow all applicable laws and regulations
    - Respect privacy and data protection laws (GDPR, CCPA, etc.)
    - Never use techniques for malicious purposes
    - Document all activities for accountability

    YOUR EXPERTISE:
    - Open Source Intelligence (OSINT) gathering and analysis
    - Social Media Intelligence (SOCMINT)
    - Corporate infrastructure mapping via public sources
    - Email harvesting and pattern analysis
    - Username enumeration across platforms
    - Phishing awareness training campaign design
    - Pretext development for authorized testing
    - Physical security assessment planning
    - Voice phishing (vishing) assessment planning
    - Data breach impact analysis
    - Employee security awareness evaluation

    OSINT METHODOLOGY:
    1. TARGET IDENTIFICATION
       - Identify target organization scope
       - Define information gathering objectives
       - Map digital footprint
       - Identify key personnel

    2. PASSIVE RECONNAISSANCE
       - Corporate website analysis
       - Social media presence mapping
       - Job postings analysis (technology stack)
       - Press releases and news articles
       - Public records and filings

    3. ACTIVE RECONNAISSANCE (NON-INTRUSIVE)
       - DNS enumeration
       - Email harvesting
       - Username enumeration
       - Technology fingerprinting

    4. ANALYSIS
       - Pattern identification
       - Attack surface mapping
       - Security control inference
       - Risk assessment

    OSINT DATA SOURCES:
    Corporate:
    - Official websites and careers pages
    - LinkedIn company pages and employee profiles
    - Glassdoor reviews and salaries
    - Crunchbase funding and leadership
    - SEC filings (for public companies)
    - Patent databases
    - Job postings (technology stack)

    Technical:
    - DNS records (MX, SPF, DMARC, DKIM)
    - SSL/TLS certificate transparency logs
    - WHOIS records
    - GitHub/GitLab repositories
    - Shodan/Censys scans
    - Wayback Machine archives

    Social Media:
    - LinkedIn (professional network)
    - Twitter/X (announcements, employees)
    - Facebook/Instagram (company culture)
    - YouTube (presentations, training)
    - Reddit (employee discussions)

    EMAIL HARVESTING TECHNIQUES:
    - Pattern identification: firstname.lastname, firstinitiallastname, etc.
    - Email finder services (Hunter.io, VoilaNorbert)
    - Google dorking for email addresses
    - WHOIS and DNS records
    - Data breach databases
    - Corporate website scraping

    USERNAME ENUMERATION:
    - Cross-platform username correlation
    - Social media platform coverage
    - Forum and community participation
    - Developer platform presence (GitHub, StackOverflow)
    - Gaming platform usernames

    PHISHING ASSESSMENT FRAMEWORK (AUTHORIZED ONLY):
    1. PLANNING PHASE
       - Define objectives (awareness vs. technical testing)
       - Identify target groups
       - Set success metrics
       - Establish escalation procedures
       - Get explicit written authorization

    2. RECONNAISSANCE PHASE
       - Harvest target email addresses
       - Analyze email patterns
       - Identify authoritative personas
       - Study communication style

    3. PRETEXT DEVELOPMENT
       - Create believable scenarios
       - Develop authentic-looking materials
       - Ensure educational value
       - Plan safe landing pages

    4. EXECUTION PHASE
       - Schedule sending times
       - Monitor delivery rates
       - Track click rates
       - Record credential entry (if in scope)

    5. ANALYSIS PHASE
       - Calculate click rates
       - Identify high-risk groups
       - Document successful techniques
       - Provide recommendations

    RULES:
    - NEVER conduct phishing without explicit written authorization
    - ALWAYS include educational component in phishing tests
    - NEVER use real credentials obtained during testing
    - ALWAYS provide clear reporting on who clicked/entered data
    - NEVER target individuals outside defined scope
    - ALWAYS respect opt-out requests immediately
    - NEVER use real customer data in templates
    - ALWAYS have incident response ready during tests

    ETHICAL BOUNDARIES:
    - No exploitation of personal tragedies
    - No impersonation of law enforcement
    - No threats or intimidation
    - No malware distribution
    - No data exfiltration beyond scope
    - No harassment or repeated contact

    REPORT FORMAT:
    1. Executive Summary
    2. Scope and Methodology
    3. OSINT Findings Summary
    4. Attack Surface Analysis
    5. Phishing Assessment Results (if authorized)
    6. Risk Ratings
    7. Recommendations
    8. Appendices (IOCs, detailed findings)
    """

    def __init__(self, name: str = "Social Engineering Expert", orchestrator=None, zen_orchestrator=None):
        super().__init__(name, AgentRole.RESEARCHER, orchestrator)
        self.zen_orchestrator = zen_orchestrator
        self.osint_data = {}
        self.findings = []

        # Register message handlers
        self.register_handler("osint_gather", self._handle_osint_gather)
        self.register_handler("email_harvest", self._handle_email_harvest)
        self.register_handler("username_enum", self._handle_username_enum)
        self.register_handler("phishing_assess", self._handle_phishing_assess)
        self.register_handler("pretext_develop", self._handle_pretext_develop)
        self.register_handler("breach_check", self._handle_breach_check)

    async def _handle_osint_gather(self, msg: AgentMessage):
        """Handle OSINT gathering request"""
        target = msg.context.get("target")
        scope = msg.context.get("scope", ["corporate", "technical", "social"])

        logger.info(f"[SocialEngExpert:{self.name}] Gathering OSINT for {target}")

        results = await self._gather_osint(target, scope)

        await self.send_message(
            content=f"OSINT gathering complete. Data points: {results['data_points']}",
            recipient=msg.sender,
            msg_type="osint_results",
            context={"results": results},
        )

    async def _handle_email_harvest(self, msg: AgentMessage):
        """Handle email harvesting"""
        domain = msg.context.get("domain")
        company = msg.context.get("company")

        logger.info(f"[SocialEngExpert:{self.name}] Harvesting emails for {domain}")

        results = await self._harvest_emails(domain, company)

        await self.send_message(
            content=f"Email harvesting complete. Found {len(results['emails'])} emails, Pattern: {results['pattern']}",
            recipient=msg.sender,
            msg_type="email_harvest_results",
            context={"results": results},
        )

    async def _handle_username_enum(self, msg: AgentMessage):
        """Handle username enumeration"""
        username = msg.context.get("username")
        platforms = msg.context.get("platforms", ["all"])

        logger.info(f"[SocialEngExpert:{self.name}] Enumerating username: {username}")

        results = await self._enumerate_username(username, platforms)

        await self.send_message(
            content=f"Username enumeration complete. Found on {len(results['found_on'])} platforms",
            recipient=msg.sender,
            msg_type="username_enum_results",
            context={"results": results},
        )

    async def _handle_phishing_assess(self, msg: AgentMessage):
        """Handle phishing assessment planning"""
        target_org = msg.context.get("target_org")
        auth_status = msg.context.get("authorized", False)

        if not auth_status:
            await self.send_message(
                content="ERROR: Phishing assessment requires explicit written authorization",
                recipient=msg.sender,
                msg_type="error",
                context={"error": "authorization_required"},
            )
            return

        logger.info(f"[SocialEngExpert:{self.name}] Planning phishing assessment for {target_org}")

        results = await self._plan_phishing_assessment(target_org)

        await self.send_message(
            content=f"Phishing assessment plan created. Scenarios: {len(results['scenarios'])}",
            recipient=msg.sender,
            msg_type="phishing_plan_results",
            context={"results": results},
        )

    async def _handle_pretext_develop(self, msg: AgentMessage):
        """Handle pretext development"""
        scenario = msg.context.get("scenario")
        target_info = msg.context.get("target_info", {})

        logger.info(f"[SocialEngExpert:{self.name}] Developing pretext for scenario: {scenario}")

        results = await self._develop_pretext(scenario, target_info)

        await self.send_message(
            content=f"Pretext development complete. Risk level: {results['risk_level']}",
            recipient=msg.sender,
            msg_type="pretext_results",
            context={"results": results},
        )

    async def _handle_breach_check(self, msg: AgentMessage):
        """Handle data breach check"""
        emails = msg.context.get("emails", [])
        domain = msg.context.get("domain")

        logger.info(f"[SocialEngExpert:{self.name}] Checking data breaches")

        results = await self._check_data_breaches(emails, domain)

        await self.send_message(
            content=f"Breach check complete. Compromised accounts: {len(results['compromised'])}",
            recipient=msg.sender,
            msg_type="breach_check_results",
            context={"results": results},
        )

    async def _gather_osint(self, target: str, scope: List[str]) -> Dict[str, Any]:
        """Gather OSINT on target"""
        results = {
            "target": target,
            "scope": scope,
            "data_points": 0,
            "corporate": {},
            "technical": {},
            "social": {},
            "employees": [],
            "technologies": [],
            "findings": [],
        }

        if "corporate" in scope:
            results["corporate"] = {
                "description": "Technology company specializing in cloud solutions",
                "founded": "2015",
                "employees": "500-1000",
                "headquarters": "San Francisco, CA",
                "website": f"https://www.{target}",
            }
            results["data_points"] += 5

        if "technical" in scope:
            results["technical"] = {
                "dns_records": [f"mail.{target}", f"www.{target}", f"api.{target}"],
                "mx_records": ["google.com"],
                "technologies": ["AWS", "CloudFlare", "WordPress"],
                "ssl_grade": "A",
            }
            results["technologies"] = results["technical"]["technologies"]
            results["data_points"] += 4

        if "social" in scope:
            results["social"] = {"linkedin_followers": 5000, "twitter_handle": f"@{target}", "job_openings": 15}
            results["data_points"] += 3

        # Simulate employee discovery
        results["employees"] = [
            {"name": "John Smith", "title": "CTO", "linkedin": f"linkedin.com/in/jsmith-{target}"},
            {"name": "Jane Doe", "title": "Head of Security", "linkedin": f"linkedin.com/in/jdoe-{target}"},
        ]

        return results

    async def _harvest_emails(self, domain: str, company: Optional[str]) -> Dict[str, Any]:
        """Harvest email addresses"""
        results = {"domain": domain, "company": company or domain, "emails": [], "pattern": None, "sources": []}

        # Simulate email discovery
        common_patterns = ["firstname.lastname", "firstinitiallastname", "firstname_lastname"]

        results["pattern"] = common_patterns[0]

        # Simulate found emails
        results["emails"] = [
            {"email": f"john.smith@{domain}", "source": "linkedin", "position": "CTO"},
            {"email": f"jane.doe@{domain}", "source": "hunter.io", "position": "Security Head"},
            {"email": f"info@{domain}", "source": "website", "position": "General"},
        ]

        results["sources"] = ["LinkedIn", "Hunter.io", "Corporate Website"]

        return results

    async def _enumerate_username(self, username: str, platforms: List[str]) -> Dict[str, Any]:
        """Enumerate username across platforms"""
        results = {"username": username, "platforms_checked": platforms, "found_on": [], "not_found_on": [], "profiles": {}}

        # Simulate platform checks
        all_platforms = {
            "twitter": f"https://twitter.com/{username}",
            "github": f"https://github.com/{username}",
            "linkedin": f"https://linkedin.com/in/{username}",
            "instagram": f"https://instagram.com/{username}",
            "facebook": f"https://facebook.com/{username}",
        }

        if "all" in platforms:
            platforms = list(all_platforms.keys())

        for platform in platforms:
            if platform in all_platforms:
                # Simulate found/not found
                if platform in ["github", "twitter"]:
                    results["found_on"].append(platform)
                    results["profiles"][platform] = {"url": all_platforms[platform], "exists": True}
                else:
                    results["not_found_on"].append(platform)

        return results

    async def _plan_phishing_assessment(self, target_org: str) -> Dict[str, Any]:
        """Plan authorized phishing assessment"""
        results = {"target": target_org, "scenarios": [], "risk_level": "medium", "recommendations": []}

        # Pre-defined safe scenarios for authorized testing
        scenarios = [
            {
                "name": "Password Reset",
                "description": "Simulate password reset email",
                "difficulty": "easy",
                "educational_value": "high",
                "red_flags": ["Generic greeting", "Urgency", "Suspicious link"],
            },
            {
                "name": "IT Support",
                "description": "IT notification about mailbox quota",
                "difficulty": "medium",
                "educational_value": "high",
                "red_flags": ["External sender", "Unusual request", "Link to external site"],
            },
            {
                "name": "Training Notification",
                "description": "Required security training notification",
                "difficulty": "hard",
                "educational_value": "very high",
                "red_flags": ["Unexpected timing", "Unusual URL", "Request for credentials"],
            },
        ]

        results["scenarios"] = scenarios
        results["recommendations"] = [
            "Start with easy scenario for baseline metrics",
            "Include immediate training for clickers",
            "Report metrics without individual naming",
            "Provide positive reinforcement for reporters",
        ]

        return results

    async def _develop_pretext(self, scenario: str, target_info: Dict) -> Dict[str, Any]:
        """Develop pretext for social engineering"""
        results = {"scenario": scenario, "target_info": target_info, "pretext": {}, "risk_level": "medium", "indicators": []}

        # Scenario templates
        templates = {
            "it_support": {
                "persona": "IT Support Specialist",
                "backstory": "New IT contractor helping with system migration",
                "approach": "Professional, helpful, slightly urgent",
                "questions": ["Can you verify your employee ID?", "What department are you in?"],
            },
            "vendor": {
                "persona": "Software Vendor Representative",
                "backstory": "Renewing software license agreement",
                "approach": "Business-focused, time-sensitive",
                "questions": ["Who handles software procurement?", "When does your current license expire?"],
            },
        }

        if scenario in templates:
            results["pretext"] = templates[scenario]

        return results

    async def _check_data_breaches(self, emails: List[str], domain: Optional[str]) -> Dict[str, Any]:
        """Check for data breach exposure"""
        results = {"emails_checked": len(emails), "domain": domain, "compromised": [], "safe": [], "breaches_found": []}

        # Simulate breach check
        for email in emails:
            # Check if email is in breach databases
            is_compromised = "john" in email  # Simulated logic

            if is_compromised:
                results["compromised"].append(
                    {
                        "email": email,
                        "breaches": ["Collection#1", "LinkedIn_2012"],
                        "exposed_data": ["email", "password_hash"],
                        "last_breach": "2019-01-01",
                    }
                )
                results["breaches_found"].extend(["Collection#1", "LinkedIn_2012"])
            else:
                results["safe"].append(email)

        results["breaches_found"] = list(set(results["breaches_found"]))

        return results

    def analyze(self, target: Optional[str], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Persona-specific analysis logic for OSINT findings.

        Args:
            target: The target organization/individual
            findings: List of OSINT findings

        Returns:
            Analysis results with attack surface assessment
        """
        analysis = {
            "total_findings": len(findings),
            "attack_surface": {},
            "risk_indicators": [],
            "exposed_data": [],
            "phishing_likelihood": "low",
            "recommendations": [],
        }

        # Calculate attack surface
        exposed_emails = 0
        exposed_employees = 0
        tech_stack_exposed = False

        for finding in findings:
            f_type = finding.get("type")

            if f_type == "email":
                exposed_emails += 1
            elif f_type == "employee":
                exposed_employees += 1
            elif f_type == "technology":
                tech_stack_exposed = True

        analysis["attack_surface"] = {
            "exposed_emails": exposed_emails,
            "exposed_employees": exposed_employees,
            "tech_stack_exposed": tech_stack_exposed,
            "social_media_presence": len([f for f in findings if f.get("type") == "social_media"]),
        }

        # Risk indicators
        if exposed_emails > 10:
            analysis["risk_indicators"].append("Large number of exposed email addresses")

        if tech_stack_exposed:
            analysis["risk_indicators"].append("Technology stack exposed in job postings")

        # Phishing likelihood
        if exposed_emails > 20 and exposed_employees > 5:
            analysis["phishing_likelihood"] = "high"
        elif exposed_emails > 5:
            analysis["phishing_likelihood"] = "medium"

        # Recommendations
        analysis["recommendations"] = self._generate_osint_recommendations(analysis)

        return analysis

    def _generate_osint_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate OSINT-specific recommendations"""
        recommendations = []

        if analysis["attack_surface"]["exposed_emails"] > 10:
            recommendations.append("Implement email obfuscation on public-facing websites")
            recommendations.append("Use contact forms instead of direct email addresses")

        if analysis["attack_surface"]["tech_stack_exposed"]:
            recommendations.append("Review job postings for technology exposure")
            recommendations.append("Consider using generic terms instead of specific versions")

        if analysis["phishing_likelihood"] in ["high", "medium"]:
            recommendations.append("Implement regular phishing awareness training")
            recommendations.append("Deploy email security solutions (SPF, DKIM, DMARC)")
            recommendations.append("Establish clear verification procedures for sensitive requests")

        recommendations.append("Conduct regular OSINT assessments to monitor exposure")
        recommendations.append("Implement social media policy for employees")

        return recommendations

    async def execute_task(self, task: Dict) -> Dict:
        """Execute OSINT/social engineering task"""
        task_type = task.get("type", "")
        context = task.get("context", {})

        logger.info(f"[SocialEngExpert:{self.name}] Executing task: {task_type}")

        if task_type == "osint_gathering":
            results = await self._gather_osint(
                context.get("target"), context.get("scope", ["corporate", "technical", "social"])
            )
            analysis = self.analyze(context.get("target"), results.get("findings", []))

            return {"status": "complete", "results": results, "analysis": analysis, "agent": self.name}

        elif task_type == "email_harvest":
            results = await self._harvest_emails(context.get("domain"), context.get("company"))
            return {"status": "complete", "results": results, "agent": self.name}

        elif task_type == "breach_check":
            results = await self._check_data_breaches(context.get("emails", []), context.get("domain"))
            return {"status": "complete", "results": results, "agent": self.name}

        return {"status": "unknown_task"}
