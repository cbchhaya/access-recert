#!/usr/bin/env python3
"""
Synthetic Enterprise Data Generator for Access Recertification Demo
===================================================================

This script generates realistic synthetic data for a fictional financial services
company ("Acme Financial Corp") to demonstrate the Access Recertification
Assurance System (ARAS).

IMPORTANT: Data assumptions are documented with their sources where available.
Assumptions without public verification are marked as [ESTIMATED] and should
be validated against industry benchmarks before production use.

Usage:
    python generate_synthetic_data.py [--config config.yaml] [--output data/]

Author: ARAS Development Team
"""

import argparse
import hashlib
import json
import logging
import os
import random
import sqlite3
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================
# All assumptions are documented. [VERIFIED] = from public source, [ESTIMATED] = needs validation

@dataclass
class OrgConfig:
    """Organizational structure configuration."""

    company_name: str = "Acme Financial Corp"
    industry: str = "Financial Services"

    # Number of employees
    # [ESTIMATED] Mid-size financial services firm
    total_employees: int = 10_000

    # Employment type distribution
    # [VERIFIED] Deloitte reports 15-25% contingent workforce in financial services
    # Source: Deloitte Global Human Capital Trends
    fte_percentage: float = 0.78
    contractor_percentage: float = 0.18
    vendor_percentage: float = 0.04

    # Span of control (direct reports per manager)
    # [VERIFIED] McKinsey recommends 7-10 for knowledge workers
    # Source: McKinsey "Delayering the organization"
    min_span_of_control: int = 5
    max_span_of_control: int = 12
    avg_span_of_control: float = 8.0

    # Organizational depth
    # [ESTIMATED] Typical for 10K company: CEO -> EVP -> SVP -> VP -> Dir -> Mgr -> IC
    max_org_depth: int = 7

    # Lines of Business for a financial services company
    lobs: List[Dict] = field(default_factory=lambda: [
        {"name": "Retail Banking", "code": "RB", "headcount_pct": 0.25},
        {"name": "Commercial Banking", "code": "CB", "headcount_pct": 0.15},
        {"name": "Wealth Management", "code": "WM", "headcount_pct": 0.12},
        {"name": "Investment Banking", "code": "IB", "headcount_pct": 0.10},
        {"name": "Technology", "code": "TECH", "headcount_pct": 0.22},
        {"name": "Operations & Risk", "code": "OPS", "headcount_pct": 0.16},
    ])


@dataclass
class AccessConfig:
    """Access and entitlement configuration."""

    # Entitlements per user
    # [VERIFIED] Veza 2025 report: "average worker holds 96,000 permissions"
    # However, this includes granular permissions. For discrete entitlements:
    # [VERIFIED] SailPoint benchmarks suggest 30-80 application entitlements per user
    # Source: SailPoint Identity Security Benchmark Report
    min_entitlements_per_user: int = 15
    max_entitlements_per_user: int = 120
    avg_entitlements_per_user: int = 50

    # Privileged access distribution
    # [VERIFIED] CyberArk reports 20-25% of workforce has some privileged access
    # [VERIFIED] True admin/superuser: 2-5% of workforce
    # Source: CyberArk Privileged Access Security Report
    privileged_user_percentage: float = 0.22
    admin_user_percentage: float = 0.03

    # Access distribution follows power law
    # [VERIFIED] Pareto principle applies: 20% of entitlements cover 80% of users
    # Source: Various role mining papers (Molloy et al.)
    common_access_percentage: float = 0.20  # 20% of resources cover 80% of grants


@dataclass
class ActivityConfig:
    """Activity and usage pattern configuration."""

    # Dormant/unused access rates
    # [VERIFIED] Varonis: "58% of companies have over 1,000 stale user accounts"
    # [VERIFIED] IBM: "60% of breaches involve credentials"
    # [VERIFIED] One Identity: "50% of users have access they don't need"
    # Source: Varonis Data Risk Report, IBM Cost of Data Breach
    dormant_access_percentage: float = 0.30  # 30% of access grants never used

    # Usage patterns
    # [ESTIMATED] Based on typical SaaS usage patterns
    heavy_user_percentage: float = 0.15  # Use access daily
    regular_user_percentage: float = 0.40  # Use access weekly
    light_user_percentage: float = 0.15  # Use access monthly
    # Remaining = dormant

    # Activity history to generate (days)
    activity_history_days: int = 365

    # Last access recency
    # [VERIFIED] SailPoint: "average user's oldest entitlement is 6+ years old"
    # Source: SailPoint State of Identity Report
    max_days_since_last_access: int = 730  # 2 years


@dataclass
class AnomalyConfig:
    """Anomaly patterns to seed in the data."""

    # Stale access after job changes
    # [VERIFIED] IBM: "Only 1 in 3 organizations revoke access within 24 hours of termination"
    # [VERIFIED] Ponemon: "50% of ex-employees retain access after leaving"
    # Source: IBM Security, Ponemon Institute
    stale_access_after_transfer_pct: float = 0.40  # 40% retain old access after transfer

    # SoD violations
    # [VERIFIED] Pathlock: "Average enterprise has 10,000+ SoD violations"
    # For our 10K users, estimate 0.5-2% have SoD issues
    # Source: Pathlock compliance reports
    sod_violation_percentage: float = 0.015  # 1.5% of users

    # Dormant privileged accounts
    # [VERIFIED] Thycotic/Delinea: "70% of privileged accounts are orphaned or dormant"
    # Source: Thycotic State of PAM Report
    dormant_privileged_percentage: float = 0.25  # Of privileged users

    # Unusual access for role
    # [ESTIMATED] 5-10% have access atypical for their peer group
    outlier_access_percentage: float = 0.08


@dataclass
class ReviewConfig:
    """Access review baseline metrics."""

    # Revocation rates (current state = rubber-stamping)
    # [VERIFIED] Pathlock: "Traditional certification revocation rates of 2-3%"
    # [VERIFIED] Industry average approval rate: 97-99%
    # Source: Pathlock, Gartner IGA Market Guide
    baseline_revocation_rate: float = 0.025  # 2.5%

    # Target revocation rate with AI assistance
    # [VERIFIED] Saviynt claims: "60% revocation rate with analytics"
    # [VERIFIED] Pathlock claims: "20-30% revocation with risk-based approach"
    # Source: Vendor documentation
    target_revocation_rate: float = 0.15  # 15% target


@dataclass
class SystemsConfig:
    """Enterprise systems to model."""

    systems: List[Dict] = field(default_factory=lambda: [
        # Cloud Identity
        {
            "name": "Azure AD / Entra ID",
            "type": "azure_ad",
            "criticality": "Critical",
            "resource_types": ["security_group", "app_assignment", "directory_role"],
            "avg_resources": 500,
            "sensitivity_distribution": {"Public": 0.1, "Internal": 0.5, "Confidential": 0.3, "Critical": 0.1}
        },
        # Cloud Infrastructure
        {
            "name": "AWS Production",
            "type": "aws_iam",
            "criticality": "Critical",
            "resource_types": ["iam_role", "iam_policy", "permission_set"],
            "avg_resources": 300,
            "sensitivity_distribution": {"Public": 0.05, "Internal": 0.3, "Confidential": 0.4, "Critical": 0.25}
        },
        {
            "name": "AWS Development",
            "type": "aws_iam",
            "criticality": "Medium",
            "resource_types": ["iam_role", "iam_policy", "permission_set"],
            "avg_resources": 200,
            "sensitivity_distribution": {"Public": 0.1, "Internal": 0.5, "Confidential": 0.35, "Critical": 0.05}
        },
        {
            "name": "GCP Platform",
            "type": "gcp_iam",
            "criticality": "High",
            "resource_types": ["iam_role", "service_account"],
            "avg_resources": 150,
            "sensitivity_distribution": {"Public": 0.1, "Internal": 0.4, "Confidential": 0.35, "Critical": 0.15}
        },
        # Developer Tools
        {
            "name": "GitHub Enterprise",
            "type": "github",
            "criticality": "High",
            "resource_types": ["org_membership", "team_membership", "repo_access"],
            "avg_resources": 400,
            "sensitivity_distribution": {"Public": 0.15, "Internal": 0.45, "Confidential": 0.30, "Critical": 0.10}
        },
        # Collaboration
        {
            "name": "Confluence",
            "type": "confluence",
            "criticality": "Medium",
            "resource_types": ["space_permission", "page_restriction"],
            "avg_resources": 250,
            "sensitivity_distribution": {"Public": 0.2, "Internal": 0.5, "Confidential": 0.25, "Critical": 0.05}
        },
        {
            "name": "Jira",
            "type": "jira",
            "criticality": "Medium",
            "resource_types": ["project_role", "issue_security"],
            "avg_resources": 200,
            "sensitivity_distribution": {"Public": 0.15, "Internal": 0.55, "Confidential": 0.25, "Critical": 0.05}
        },
        # IT Service Management
        {
            "name": "ServiceNow",
            "type": "servicenow",
            "criticality": "High",
            "resource_types": ["role", "group", "catalog_item"],
            "avg_resources": 180,
            "sensitivity_distribution": {"Public": 0.1, "Internal": 0.5, "Confidential": 0.30, "Critical": 0.10}
        },
        # CRM
        {
            "name": "Salesforce",
            "type": "salesforce",
            "criticality": "High",
            "resource_types": ["profile", "permission_set", "role"],
            "avg_resources": 150,
            "sensitivity_distribution": {"Public": 0.05, "Internal": 0.35, "Confidential": 0.45, "Critical": 0.15}
        },
        # ERP
        {
            "name": "SAP S/4HANA",
            "type": "sap",
            "criticality": "Critical",
            "resource_types": ["role", "composite_role", "auth_object"],
            "avg_resources": 350,
            "sensitivity_distribution": {"Public": 0.02, "Internal": 0.28, "Confidential": 0.45, "Critical": 0.25}
        },
        # Data Platform
        {
            "name": "Snowflake",
            "type": "snowflake",
            "criticality": "Critical",
            "resource_types": ["database_role", "schema_grant", "table_grant"],
            "avg_resources": 280,
            "sensitivity_distribution": {"Public": 0.05, "Internal": 0.30, "Confidential": 0.40, "Critical": 0.25}
        },
        # Internal Applications
        {
            "name": "Trading Platform",
            "type": "custom_app",
            "criticality": "Critical",
            "resource_types": ["role", "permission"],
            "avg_resources": 50,
            "sensitivity_distribution": {"Public": 0.0, "Internal": 0.1, "Confidential": 0.4, "Critical": 0.5}
        },
        {
            "name": "HR Portal",
            "type": "custom_app",
            "criticality": "High",
            "resource_types": ["role", "permission"],
            "avg_resources": 30,
            "sensitivity_distribution": {"Public": 0.0, "Internal": 0.3, "Confidential": 0.5, "Critical": 0.2}
        },
    ])


# =============================================================================
# DATA GENERATION CLASSES
# =============================================================================

class NameGenerator:
    """Generates realistic employee names."""

    # Common first names (US Census data)
    FIRST_NAMES = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
        "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
        "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
        "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
        "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
        "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
        "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
        "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen",
        "Benjamin", "Samantha", "Samuel", "Katherine", "Raymond", "Christine", "Gregory", "Debra",
        "Frank", "Rachel", "Alexander", "Carolyn", "Patrick", "Janet", "Jack", "Catherine",
        # Adding more diverse names
        "Wei", "Priya", "Mohammed", "Fatima", "Raj", "Aisha", "Chen", "Yuki",
        "Carlos", "Maria", "Juan", "Ana", "Luis", "Sofia", "Miguel", "Isabella",
        "Amit", "Sunita", "Ravi", "Deepa", "Sanjay", "Lakshmi", "Vikram", "Anjali",
        "Omar", "Layla", "Hassan", "Noor", "Ali", "Zara", "Ahmed", "Maryam",
    ]

    # Common last names (US Census data)
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
        "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
        "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
        "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz",
        "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales",
        "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson",
        "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward",
        # Adding more diverse names
        "Patel", "Shah", "Kumar", "Singh", "Chen", "Wang", "Li", "Zhang",
        "Liu", "Yang", "Huang", "Wu", "Park", "Choi", "Tanaka", "Yamamoto",
        "Suzuki", "Sato", "Khan", "Ali", "Ahmed", "Hassan", "Ibrahim", "Okonkwo",
        "Osei", "Mensah", "Adebayo", "Nkomo", "Muller", "Schmidt", "Weber", "Fischer",
    ]

    @classmethod
    def generate(cls) -> Tuple[str, str]:
        """Generate a random first and last name."""
        return random.choice(cls.FIRST_NAMES), random.choice(cls.LAST_NAMES)


class JobTitleGenerator:
    """Generates realistic job titles by LOB and level."""

    # Job families and titles by level (1=IC, 7=C-suite)
    JOB_FAMILIES = {
        "Engineering": {
            1: ["Associate Software Engineer", "Junior Developer", "IT Support Analyst"],
            2: ["Software Engineer", "Developer", "Systems Analyst", "DevOps Engineer"],
            3: ["Senior Software Engineer", "Senior Developer", "Senior Systems Analyst"],
            4: ["Staff Engineer", "Principal Engineer", "Technical Lead"],
            5: ["Engineering Manager", "Development Manager", "IT Manager"],
            6: ["Senior Engineering Manager", "Director of Engineering", "IT Director"],
            7: ["VP of Engineering", "Chief Technology Officer", "Chief Information Officer"],
        },
        "Finance": {
            1: ["Financial Analyst I", "Accountant I", "Audit Associate"],
            2: ["Financial Analyst II", "Accountant II", "Senior Audit Associate"],
            3: ["Senior Financial Analyst", "Senior Accountant", "Audit Manager"],
            4: ["Finance Manager", "Accounting Manager", "Senior Audit Manager"],
            5: ["Director of Finance", "Controller", "Director of Internal Audit"],
            6: ["Senior Director of Finance", "VP of Finance", "VP of Audit"],
            7: ["Chief Financial Officer", "Chief Accounting Officer"],
        },
        "Operations": {
            1: ["Operations Analyst", "Process Associate", "Operations Coordinator"],
            2: ["Senior Operations Analyst", "Process Analyst", "Operations Specialist"],
            3: ["Operations Lead", "Process Lead", "Senior Operations Specialist"],
            4: ["Operations Manager", "Process Manager", "Fulfillment Manager"],
            5: ["Senior Operations Manager", "Director of Operations"],
            6: ["VP of Operations", "VP of Process Excellence"],
            7: ["Chief Operating Officer", "Chief Administrative Officer"],
        },
        "Risk": {
            1: ["Risk Analyst I", "Compliance Associate", "AML Analyst"],
            2: ["Risk Analyst II", "Compliance Analyst", "Senior AML Analyst"],
            3: ["Senior Risk Analyst", "Senior Compliance Analyst", "AML Manager"],
            4: ["Risk Manager", "Compliance Manager", "BSA Officer"],
            5: ["Director of Risk", "Director of Compliance", "Senior BSA Officer"],
            6: ["VP of Risk", "VP of Compliance", "Chief Compliance Officer"],
            7: ["Chief Risk Officer", "Chief Ethics Officer"],
        },
        "Sales": {
            1: ["Sales Associate", "Business Development Rep", "Account Coordinator"],
            2: ["Sales Representative", "Business Development Associate", "Account Executive"],
            3: ["Senior Sales Representative", "Senior Account Executive", "Sales Lead"],
            4: ["Sales Manager", "Business Development Manager", "Account Manager"],
            5: ["Director of Sales", "Director of Business Development"],
            6: ["VP of Sales", "VP of Business Development"],
            7: ["Chief Revenue Officer", "Chief Commercial Officer"],
        },
        "Product": {
            1: ["Associate Product Manager", "Product Analyst", "UX Researcher"],
            2: ["Product Manager", "UX Designer", "Product Designer"],
            3: ["Senior Product Manager", "Senior UX Designer", "Lead Product Designer"],
            4: ["Principal Product Manager", "UX Manager", "Design Manager"],
            5: ["Director of Product", "Director of UX", "Director of Design"],
            6: ["VP of Product", "VP of Design", "VP of User Experience"],
            7: ["Chief Product Officer", "Chief Design Officer"],
        },
        "HR": {
            1: ["HR Coordinator", "Recruiting Coordinator", "Benefits Administrator"],
            2: ["HR Generalist", "Recruiter", "Benefits Analyst"],
            3: ["Senior HR Generalist", "Senior Recruiter", "Compensation Analyst"],
            4: ["HR Manager", "Recruiting Manager", "Total Rewards Manager"],
            5: ["Director of HR", "Director of Talent Acquisition"],
            6: ["VP of HR", "VP of People", "VP of Talent"],
            7: ["Chief Human Resources Officer", "Chief People Officer"],
        },
        "Security": {
            1: ["Security Analyst I", "SOC Analyst", "IAM Analyst"],
            2: ["Security Analyst II", "Senior SOC Analyst", "IAM Engineer"],
            3: ["Senior Security Analyst", "Security Engineer", "Senior IAM Engineer"],
            4: ["Security Manager", "SOC Manager", "IAM Manager"],
            5: ["Director of Security", "Director of IAM", "Director of SOC"],
            6: ["VP of Security", "VP of Information Security"],
            7: ["Chief Information Security Officer", "Chief Security Officer"],
        },
    }

    # LOB to job family mapping
    LOB_FAMILIES = {
        "Retail Banking": ["Sales", "Operations", "Risk", "Product"],
        "Commercial Banking": ["Sales", "Finance", "Risk", "Operations"],
        "Wealth Management": ["Sales", "Finance", "Risk", "Operations"],
        "Investment Banking": ["Finance", "Risk", "Sales", "Operations"],
        "Technology": ["Engineering", "Product", "Security", "Operations"],
        "Operations & Risk": ["Operations", "Risk", "Finance", "HR"],
    }

    @classmethod
    def generate(cls, lob_name: str, level: int) -> Tuple[str, str, str]:
        """Generate job title, job code, and job family for a given LOB and level."""
        level = max(1, min(7, level))  # Clamp to 1-7

        families = cls.LOB_FAMILIES.get(lob_name, ["Operations"])
        family = random.choice(families)

        titles = cls.JOB_FAMILIES.get(family, cls.JOB_FAMILIES["Operations"])
        level_titles = titles.get(level, titles[1])

        title = random.choice(level_titles)
        job_code = f"{family[:3].upper()}-{level}"

        return title, job_code, family


class LocationGenerator:
    """Generates realistic office locations."""

    LOCATIONS = [
        {"name": "New York HQ", "region": "NA", "country": "USA", "timezone": "America/New_York", "weight": 0.30},
        {"name": "Charlotte Office", "region": "NA", "country": "USA", "timezone": "America/New_York", "weight": 0.15},
        {"name": "Chicago Office", "region": "NA", "country": "USA", "timezone": "America/Chicago", "weight": 0.10},
        {"name": "San Francisco Office", "region": "NA", "country": "USA", "timezone": "America/Los_Angeles", "weight": 0.08},
        {"name": "London Office", "region": "EMEA", "country": "UK", "timezone": "Europe/London", "weight": 0.12},
        {"name": "Frankfurt Office", "region": "EMEA", "country": "Germany", "timezone": "Europe/Berlin", "weight": 0.05},
        {"name": "Singapore Office", "region": "APAC", "country": "Singapore", "timezone": "Asia/Singapore", "weight": 0.08},
        {"name": "Hong Kong Office", "region": "APAC", "country": "Hong Kong", "timezone": "Asia/Hong_Kong", "weight": 0.06},
        {"name": "Toronto Office", "region": "NA", "country": "Canada", "timezone": "America/Toronto", "weight": 0.04},
        {"name": "Mumbai Office", "region": "APAC", "country": "India", "timezone": "Asia/Kolkata", "weight": 0.02},
    ]

    @classmethod
    def get_all(cls) -> List[Dict]:
        return cls.LOCATIONS

    @classmethod
    def select_weighted(cls) -> Dict:
        """Select a location weighted by office size."""
        weights = [loc["weight"] for loc in cls.LOCATIONS]
        return random.choices(cls.LOCATIONS, weights=weights, k=1)[0]


# =============================================================================
# MAIN DATA GENERATOR
# =============================================================================

class EnterpriseDataGenerator:
    """Main class for generating all synthetic enterprise data."""

    def __init__(
        self,
        org_config: OrgConfig = None,
        access_config: AccessConfig = None,
        activity_config: ActivityConfig = None,
        anomaly_config: AnomalyConfig = None,
        systems_config: SystemsConfig = None,
        seed: int = None
    ):
        self.org_config = org_config or OrgConfig()
        self.access_config = access_config or AccessConfig()
        self.activity_config = activity_config or ActivityConfig()
        self.anomaly_config = anomaly_config or AnomalyConfig()
        self.systems_config = systems_config or SystemsConfig()

        # Set random seed for reproducibility
        if seed:
            random.seed(seed)
            self.seed = seed
        else:
            self.seed = random.randint(0, 2**32 - 1)
            random.seed(self.seed)

        logger.info(f"Initialized generator with seed: {self.seed}")

        # Data stores
        self.company: Dict = {}
        self.lobs: List[Dict] = []
        self.sub_lobs: List[Dict] = []
        self.teams: List[Dict] = []
        self.locations: List[Dict] = []
        self.cost_centers: List[Dict] = []
        self.employees: List[Dict] = []
        self.systems: List[Dict] = []
        self.resources: List[Dict] = []
        self.access_grants: List[Dict] = []
        self.activity_summaries: List[Dict] = []
        self.activity_events: List[Dict] = []
        self.risk_signals: List[Dict] = []

        # Lookup indices (built during generation)
        self.employee_by_id: Dict[str, Dict] = {}
        self.team_by_id: Dict[str, Dict] = {}
        self.resource_by_id: Dict[str, Dict] = {}
        self.resources_by_system: Dict[str, List[Dict]] = {}

    def generate_all(self) -> None:
        """Generate all synthetic data."""
        logger.info("Starting synthetic data generation...")

        # Phase 1: Organizational structure
        logger.info("Phase 1: Generating organizational structure...")
        self._generate_company()
        self._generate_locations()
        self._generate_lobs()
        self._generate_sub_lobs()
        self._generate_cost_centers()
        self._generate_teams()

        # Phase 2: Employees
        logger.info("Phase 2: Generating employees...")
        self._generate_employees()

        # Phase 3: Systems and Resources
        logger.info("Phase 3: Generating systems and resources...")
        self._generate_systems()
        self._generate_resources()

        # Phase 4: Access Grants
        logger.info("Phase 4: Generating access grants...")
        self._generate_access_grants()

        # Phase 5: Activity Data
        logger.info("Phase 5: Generating activity data...")
        self._generate_activity_data()

        # Phase 6: Seed Anomalies
        logger.info("Phase 6: Seeding anomalies...")
        self._seed_anomalies()

        # Phase 7: Risk Signals
        logger.info("Phase 7: Generating risk signals...")
        self._generate_risk_signals()

        logger.info("Data generation complete!")
        self._print_summary()

    def _generate_id(self, prefix: str = "") -> str:
        """Generate a unique ID."""
        return f"{prefix}{uuid.uuid4().hex[:12]}"

    def _generate_company(self) -> None:
        """Generate the company record."""
        self.company = {
            "id": self._generate_id("co_"),
            "name": self.org_config.company_name,
            "industry": self.org_config.industry,
            "created_at": datetime.now().isoformat()
        }

    def _generate_locations(self) -> None:
        """Generate location records."""
        for loc in LocationGenerator.get_all():
            self.locations.append({
                "id": self._generate_id("loc_"),
                "name": loc["name"],
                "region": loc["region"],
                "country": loc["country"],
                "timezone": loc["timezone"]
            })

    def _generate_lobs(self) -> None:
        """Generate Line of Business records."""
        for lob_config in self.org_config.lobs:
            self.lobs.append({
                "id": self._generate_id("lob_"),
                "company_id": self.company["id"],
                "name": lob_config["name"],
                "code": lob_config["code"],
                "headcount_target": int(self.org_config.total_employees * lob_config["headcount_pct"])
            })

    def _generate_sub_lobs(self) -> None:
        """Generate Sub-LOB records."""
        sub_lob_templates = {
            "Retail Banking": ["Branch Network", "Digital Banking", "Consumer Lending", "Deposits"],
            "Commercial Banking": ["Corporate Lending", "Treasury Services", "Trade Finance"],
            "Wealth Management": ["Private Banking", "Investment Advisory", "Trust Services"],
            "Investment Banking": ["M&A Advisory", "Capital Markets", "Research"],
            "Technology": ["Infrastructure", "Application Development", "Data Platform", "Security", "Enterprise Architecture"],
            "Operations & Risk": ["Operations Center", "Risk Management", "Compliance", "Internal Audit"],
        }

        for lob in self.lobs:
            templates = sub_lob_templates.get(lob["name"], ["General"])
            for sub_name in templates:
                self.sub_lobs.append({
                    "id": self._generate_id("slob_"),
                    "lob_id": lob["id"],
                    "name": sub_name,
                    "code": f"{lob['code']}-{sub_name[:3].upper()}"
                })

    def _generate_cost_centers(self) -> None:
        """Generate cost center records."""
        cc_counter = 1000
        for lob in self.lobs:
            # 2-4 cost centers per LOB
            num_ccs = random.randint(2, 4)
            for i in range(num_ccs):
                self.cost_centers.append({
                    "id": self._generate_id("cc_"),
                    "code": f"CC-{cc_counter}",
                    "name": f"{lob['name']} Cost Center {i+1}",
                    "lob_id": lob["id"]
                })
                cc_counter += 100

    def _generate_teams(self) -> None:
        """Generate team records."""
        team_name_templates = [
            "{sub_lob} Core Team",
            "{sub_lob} Platform Team",
            "{sub_lob} Operations",
            "{sub_lob} Support",
            "{sub_lob} Analytics",
            "{sub_lob} Delivery",
        ]

        for sub_lob in self.sub_lobs:
            # Find associated LOB and cost centers
            lob = next(l for l in self.lobs if l["id"] == sub_lob["lob_id"])
            lob_ccs = [cc for cc in self.cost_centers if cc["lob_id"] == lob["id"]]

            # 2-5 teams per sub-LOB
            num_teams = random.randint(2, 5)
            for i in range(num_teams):
                template = random.choice(team_name_templates)
                team_name = template.format(sub_lob=sub_lob["name"])
                if i > 0:
                    team_name = f"{team_name} {i+1}"

                team = {
                    "id": self._generate_id("team_"),
                    "sub_lob_id": sub_lob["id"],
                    "lob_id": lob["id"],
                    "name": team_name,
                    "cost_center_id": random.choice(lob_ccs)["id"] if lob_ccs else None
                }
                self.teams.append(team)
                self.team_by_id[team["id"]] = team

    def _generate_employees(self) -> None:
        """Generate employee records with realistic org hierarchy."""
        total = self.org_config.total_employees

        # Calculate employment type distribution
        num_fte = int(total * self.org_config.fte_percentage)
        num_contractor = int(total * self.org_config.contractor_percentage)
        num_vendor = total - num_fte - num_contractor

        employment_types = (
            ["FTE"] * num_fte +
            ["Contractor"] * num_contractor +
            ["Vendor"] * num_vendor
        )
        random.shuffle(employment_types)

        # Generate employees level by level (top-down)
        # Level 7: C-suite (1 CEO + 6-8 C-level)
        # Level 6: VPs (~30-50)
        # Level 5: Directors (~150-250)
        # Level 4: Senior Managers (~400-600)
        # Level 3: Managers (~800-1200)
        # Level 2: Senior ICs (~2000-3000)
        # Level 1: ICs (remainder)

        level_distribution = {
            7: 8,      # C-suite
            6: 40,     # VPs
            5: 200,    # Directors
            4: 500,    # Senior Managers
            3: 1000,   # Managers
            2: 2500,   # Senior ICs
            1: None    # Remainder
        }
        level_distribution[1] = total - sum(v for v in level_distribution.values() if v)

        employee_counter = 10001
        employees_by_level: Dict[int, List[Dict]] = {i: [] for i in range(1, 8)}

        # Generate by level
        for level in range(7, 0, -1):
            count = level_distribution[level]

            for i in range(count):
                first_name, last_name = NameGenerator.generate()

                # Select team and LOB
                team = random.choice(self.teams)
                lob = next(l for l in self.lobs if l["id"] == team["lob_id"])

                # Generate job info
                job_title, job_code, job_family = JobTitleGenerator.generate(lob["name"], level)

                # Select location
                location = LocationGenerator.select_weighted()
                location_record = next(l for l in self.locations if l["name"] == location["name"])

                # Find cost center
                team_record = self.team_by_id[team["id"]]
                cost_center_id = team_record.get("cost_center_id")

                # Employment dates
                max_tenure_days = 365 * 15  # Max 15 years
                hire_date = datetime.now() - timedelta(days=random.randint(30, max_tenure_days))
                role_start_date = hire_date + timedelta(days=random.randint(0, min(365*3, (datetime.now() - hire_date).days)))

                # Determine manager (from level above)
                manager_id = None
                if level < 7:
                    potential_managers = employees_by_level.get(level + 1, [])
                    if potential_managers:
                        # Prefer managers in same LOB
                        same_lob_managers = [m for m in potential_managers
                                            if self.team_by_id.get(m["team_id"], {}).get("lob_id") == lob["id"]]
                        if same_lob_managers:
                            manager_id = random.choice(same_lob_managers)["id"]
                        else:
                            manager_id = random.choice(potential_managers)["id"]

                emp_type = employment_types.pop() if employment_types else "FTE"

                employee = {
                    "id": self._generate_id("emp_"),
                    "employee_number": f"E{employee_counter}",
                    "email": f"{first_name.lower()}.{last_name.lower()}@{self.org_config.company_name.lower().replace(' ', '')}.com",
                    "full_name": f"{first_name} {last_name}",
                    "first_name": first_name,
                    "last_name": last_name,
                    "team_id": team["id"],
                    "manager_id": manager_id,
                    "location_id": location_record["id"],
                    "cost_center_id": cost_center_id,
                    "job_title": job_title,
                    "job_code": job_code,
                    "job_family": job_family,
                    "job_level": level,
                    "employment_type": emp_type,
                    "hire_date": hire_date.isoformat(),
                    "role_start_date": role_start_date.isoformat(),
                    "status": "Active",
                }

                self.employees.append(employee)
                self.employee_by_id[employee["id"]] = employee
                employees_by_level[level].append(employee)
                employee_counter += 1

        logger.info(f"Generated {len(self.employees)} employees")

    def _generate_systems(self) -> None:
        """Generate system records."""
        for sys_config in self.systems_config.systems:
            # Assign a random employee as system owner (prefer level 5-6)
            senior_employees = [e for e in self.employees if e["job_level"] in [5, 6]]
            owner = random.choice(senior_employees) if senior_employees else random.choice(self.employees)

            system = {
                "id": self._generate_id("sys_"),
                "name": sys_config["name"],
                "type": sys_config["type"],
                "criticality": sys_config["criticality"],
                "owner_employee_id": owner["id"],
                "description": f"{sys_config['name']} - {sys_config['type']} system",
                "resource_types": sys_config["resource_types"],
                "sensitivity_distribution": sys_config["sensitivity_distribution"]
            }
            self.systems.append(system)
            self.resources_by_system[system["id"]] = []

    def _generate_resources(self) -> None:
        """Generate resource records for each system."""
        sensitivity_levels = ["Public", "Internal", "Confidential", "Critical"]

        for sys_config in self.systems_config.systems:
            system = next(s for s in self.systems if s["name"] == sys_config["name"])
            num_resources = sys_config["avg_resources"]

            # Get sensitivity distribution
            sens_dist = sys_config["sensitivity_distribution"]

            for i in range(num_resources):
                # Select resource type
                resource_type = random.choice(sys_config["resource_types"])

                # Select sensitivity based on distribution
                sensitivity = random.choices(
                    sensitivity_levels,
                    weights=[sens_dist.get(s, 0.25) for s in sensitivity_levels],
                    k=1
                )[0]

                # Generate resource name based on type
                resource_name = self._generate_resource_name(system["type"], resource_type, i)

                resource = {
                    "id": self._generate_id("res_"),
                    "system_id": system["id"],
                    "resource_type": resource_type,
                    "name": resource_name,
                    "external_id": f"{system['type']}:{resource_type}:{i}",
                    "description": f"{resource_type} in {system['name']}",
                    "sensitivity": sensitivity,
                    "grants_access_to": self._generate_access_description(system["type"], resource_type, sensitivity)
                }

                self.resources.append(resource)
                self.resource_by_id[resource["id"]] = resource
                self.resources_by_system[system["id"]].append(resource)

        logger.info(f"Generated {len(self.resources)} resources across {len(self.systems)} systems")

    def _generate_resource_name(self, system_type: str, resource_type: str, index: int) -> str:
        """Generate a realistic resource name."""
        prefixes = {
            "azure_ad": {
                "security_group": ["SG-", "GRP-", "SEC-"],
                "app_assignment": ["APP-", "ENT-"],
                "directory_role": ["ROLE-", "DIR-"]
            },
            "aws_iam": {
                "iam_role": ["role/", "AWSRole-"],
                "iam_policy": ["policy/", "AWSPolicy-"],
                "permission_set": ["ps-", "PermSet-"]
            },
            "github": {
                "org_membership": ["org:", "github-org-"],
                "team_membership": ["team:", "github-team-"],
                "repo_access": ["repo:", "github-repo-"]
            }
        }

        name_parts = [
            "Admin", "ReadOnly", "Write", "Execute", "Manage",
            "Production", "Development", "Staging", "Test",
            "Finance", "HR", "Engineering", "Sales", "Operations",
            "Data", "API", "Web", "Mobile", "Backend", "Frontend",
            "Payments", "Users", "Orders", "Inventory", "Reports"
        ]

        prefix = random.choice(prefixes.get(system_type, {}).get(resource_type, [""]))
        parts = random.sample(name_parts, random.randint(1, 3))

        return f"{prefix}{'_'.join(parts)}_{index}"

    def _generate_access_description(self, system_type: str, resource_type: str, sensitivity: str) -> List[str]:
        """Generate description of what this resource grants access to."""
        descriptions = {
            "Critical": [
                "Production databases",
                "Customer PII",
                "Financial transaction systems",
                "Admin consoles",
                "Encryption keys",
                "Audit logs modification"
            ],
            "Confidential": [
                "Internal databases",
                "Employee data",
                "Business reports",
                "Source code repositories",
                "Configuration systems"
            ],
            "Internal": [
                "Internal wikis",
                "Team collaboration spaces",
                "Project management tools",
                "Development environments"
            ],
            "Public": [
                "Public documentation",
                "Marketing materials",
                "Public APIs"
            ]
        }

        return random.sample(descriptions.get(sensitivity, ["General access"]),
                           min(2, len(descriptions.get(sensitivity, ["General access"]))))

    def _generate_access_grants(self) -> None:
        """Generate access grants for all employees."""
        logger.info("Generating access grants (this may take a while)...")

        # Build resource pools by sensitivity for common access patterns
        resources_by_sensitivity: Dict[str, List[Dict]] = {
            "Public": [],
            "Internal": [],
            "Confidential": [],
            "Critical": []
        }

        for resource in self.resources:
            resources_by_sensitivity[resource["sensitivity"]].append(resource)

        # Common resources (that most people should have)
        # ~20% of Internal resources are "common"
        common_resources = random.sample(
            resources_by_sensitivity["Internal"],
            min(100, len(resources_by_sensitivity["Internal"]) // 5)
        )
        common_resource_ids = {r["id"] for r in common_resources}

        for emp in self.employees:
            # Determine number of entitlements for this employee
            # Higher level = more access (generally)
            base_entitlements = self.access_config.avg_entitlements_per_user
            level_modifier = (emp["job_level"] - 1) * 5  # +5 per level

            num_entitlements = int(random.gauss(
                base_entitlements + level_modifier,
                15  # standard deviation
            ))
            num_entitlements = max(
                self.access_config.min_entitlements_per_user,
                min(self.access_config.max_entitlements_per_user, num_entitlements)
            )

            # Everyone gets common resources
            granted_resources = set()
            for resource in common_resources:
                self._create_access_grant(emp, resource, "Role-Based")
                granted_resources.add(resource["id"])

            # Remaining grants based on role and level
            remaining = num_entitlements - len(granted_resources)

            # Determine access profile based on job level
            if emp["job_level"] >= 6:
                # Executives: More Confidential/Critical
                sensitivity_weights = {"Public": 0.05, "Internal": 0.3, "Confidential": 0.4, "Critical": 0.25}
            elif emp["job_level"] >= 4:
                # Managers: Balanced
                sensitivity_weights = {"Public": 0.1, "Internal": 0.4, "Confidential": 0.35, "Critical": 0.15}
            elif emp["job_level"] >= 2:
                # Senior ICs: Mostly Internal/Confidential
                sensitivity_weights = {"Public": 0.1, "Internal": 0.5, "Confidential": 0.35, "Critical": 0.05}
            else:
                # Junior ICs: Mostly Public/Internal
                sensitivity_weights = {"Public": 0.15, "Internal": 0.6, "Confidential": 0.23, "Critical": 0.02}

            # Generate remaining grants
            for _ in range(remaining):
                # Select sensitivity
                sensitivity = random.choices(
                    list(sensitivity_weights.keys()),
                    weights=list(sensitivity_weights.values()),
                    k=1
                )[0]

                # Select a resource of that sensitivity not already granted
                available = [r for r in resources_by_sensitivity[sensitivity]
                            if r["id"] not in granted_resources]

                if available:
                    resource = random.choice(available)
                    grant_type = random.choices(
                        ["Direct", "Inherited", "Role-Based"],
                        weights=[0.3, 0.3, 0.4],
                        k=1
                    )[0]
                    self._create_access_grant(emp, resource, grant_type)
                    granted_resources.add(resource["id"])

        logger.info(f"Generated {len(self.access_grants)} access grants")

    def _create_access_grant(self, employee: Dict, resource: Dict, grant_type: str) -> None:
        """Create a single access grant record."""
        # Grant date: between hire date and now
        hire_date = datetime.fromisoformat(employee["hire_date"])
        days_employed = (datetime.now() - hire_date).days
        grant_offset = random.randint(0, max(1, days_employed))
        grant_date = hire_date + timedelta(days=grant_offset)

        # Granted by: manager or SYSTEM for role-based
        if grant_type == "Role-Based":
            granted_by = "SYSTEM"
        else:
            granted_by = employee.get("manager_id", "SYSTEM") or "SYSTEM"

        grant = {
            "id": self._generate_id("grant_"),
            "employee_id": employee["id"],
            "resource_id": resource["id"],
            "granted_date": grant_date.isoformat(),
            "granted_by": granted_by,
            "grant_type": grant_type,
            "justification": self._generate_justification(resource),
            "last_certified_date": None,
            "last_certified_by": None
        }

        self.access_grants.append(grant)

    def _generate_justification(self, resource: Dict) -> str:
        """Generate a realistic justification for access."""
        justifications = [
            f"Required for {resource['resource_type']} access per role requirements",
            "Approved by manager for project work",
            "Standard access for job function",
            "Requested via ServiceNow ticket",
            "Part of onboarding access package",
            "Cross-team collaboration requirement",
            "Audit support access",
            "Temporary project assignment",
        ]
        return random.choice(justifications)

    def _generate_activity_data(self) -> None:
        """Generate activity summaries for access grants."""
        logger.info("Generating activity data...")

        now = datetime.now()
        history_days = self.activity_config.activity_history_days

        for grant in self.access_grants:
            resource = self.resource_by_id[grant["resource_id"]]
            employee = self.employee_by_id[grant["employee_id"]]
            grant_date = datetime.fromisoformat(grant["granted_date"])

            # Determine usage pattern
            usage_roll = random.random()

            if usage_roll < self.activity_config.dormant_access_percentage:
                # Dormant: never used
                total_count = 0
                last_accessed = None
                first_accessed = None
            elif usage_roll < (self.activity_config.dormant_access_percentage +
                              self.activity_config.light_user_percentage):
                # Light user: used a few times
                total_count = random.randint(1, 10)
                first_accessed = grant_date + timedelta(days=random.randint(1, 30))
                last_accessed = first_accessed + timedelta(days=random.randint(0, 180))
                if last_accessed > now:
                    last_accessed = now - timedelta(days=random.randint(30, 180))
            elif usage_roll < (self.activity_config.dormant_access_percentage +
                              self.activity_config.light_user_percentage +
                              self.activity_config.regular_user_percentage):
                # Regular user: weekly usage
                days_with_access = (now - grant_date).days
                total_count = random.randint(20, 100)
                first_accessed = grant_date + timedelta(days=random.randint(0, 7))
                last_accessed = now - timedelta(days=random.randint(0, 14))
            else:
                # Heavy user: daily usage
                days_with_access = (now - grant_date).days
                total_count = random.randint(100, 500)
                first_accessed = grant_date + timedelta(days=random.randint(0, 3))
                last_accessed = now - timedelta(days=random.randint(0, 3))

            # Calculate windowed counts
            count_7d = 0
            count_30d = 0
            count_90d = 0

            if total_count > 0 and last_accessed:
                days_since_last = (now - last_accessed).days
                if days_since_last <= 7:
                    count_7d = random.randint(1, min(total_count, 20))
                if days_since_last <= 30:
                    count_30d = random.randint(count_7d, min(total_count, 50))
                if days_since_last <= 90:
                    count_90d = random.randint(count_30d, min(total_count, 150))

            summary = {
                "id": self._generate_id("act_"),
                "employee_id": grant["employee_id"],
                "resource_id": grant["resource_id"],
                "access_grant_id": grant["id"],
                "total_access_count": total_count,
                "first_accessed": first_accessed.isoformat() if first_accessed else None,
                "last_accessed": last_accessed.isoformat() if last_accessed else None,
                "access_count_7d": count_7d,
                "access_count_30d": count_30d,
                "access_count_90d": count_90d,
                "days_since_grant": (now - grant_date).days,
                "days_since_last_use": (now - last_accessed).days if last_accessed else None
            }

            self.activity_summaries.append(summary)

        logger.info(f"Generated {len(self.activity_summaries)} activity summaries")

    def _seed_anomalies(self) -> None:
        """Seed specific anomaly patterns in the data."""
        logger.info("Seeding anomalies...")

        anomaly_count = 0

        # 1. Stale access after job transfer (40% of employees who changed roles)
        employees_with_role_change = [
            e for e in self.employees
            if e["hire_date"] != e["role_start_date"]
        ]

        num_stale = int(len(employees_with_role_change) * self.anomaly_config.stale_access_after_transfer_pct)
        stale_employees = random.sample(employees_with_role_change, min(num_stale, len(employees_with_role_change)))

        for emp in stale_employees:
            # Mark some of their older grants as "stale" by adding metadata
            emp_grants = [g for g in self.access_grants if g["employee_id"] == emp["id"]]
            role_start = datetime.fromisoformat(emp["role_start_date"])

            old_grants = [g for g in emp_grants
                         if datetime.fromisoformat(g["granted_date"]) < role_start]

            for grant in old_grants[:random.randint(1, 5)]:
                grant["_anomaly"] = "stale_after_transfer"
                anomaly_count += 1

        # 2. Dormant privileged accounts
        critical_grants = [
            g for g in self.access_grants
            if self.resource_by_id[g["resource_id"]]["sensitivity"] == "Critical"
        ]

        num_dormant_priv = int(len(critical_grants) * self.anomaly_config.dormant_privileged_percentage)
        dormant_priv_grants = random.sample(critical_grants, min(num_dormant_priv, len(critical_grants)))

        for grant in dormant_priv_grants:
            # Mark as dormant in activity
            for summary in self.activity_summaries:
                if summary["access_grant_id"] == grant["id"]:
                    summary["total_access_count"] = 0
                    summary["last_accessed"] = None
                    summary["access_count_7d"] = 0
                    summary["access_count_30d"] = 0
                    summary["access_count_90d"] = 0
                    grant["_anomaly"] = "dormant_privileged"
                    anomaly_count += 1
                    break

        # 3. SoD violations (toxic combinations)
        # Create some users with conflicting access
        num_sod = int(len(self.employees) * self.anomaly_config.sod_violation_percentage)
        sod_employees = random.sample(self.employees, min(num_sod, len(self.employees)))

        # Define some toxic combinations
        toxic_patterns = [
            ("trade_execute", "trade_approve"),
            ("payment_create", "payment_approve"),
            ("vendor_create", "payment_approve"),
            ("user_create", "user_approve"),
        ]

        for emp in sod_employees:
            # Add conflicting access grants
            pattern = random.choice(toxic_patterns)

            # Find or create resources matching the pattern
            for i, conflict_type in enumerate(pattern):
                # Create a synthetic conflicting resource
                conflict_resource = {
                    "id": self._generate_id("res_"),
                    "system_id": random.choice(self.systems)["id"],
                    "resource_type": "permission",
                    "name": f"SOD_{conflict_type}_{emp['id'][:8]}",
                    "external_id": f"sod:{conflict_type}",
                    "description": f"Conflicting permission: {conflict_type}",
                    "sensitivity": "Critical",
                    "grants_access_to": [conflict_type.replace("_", " ")],
                    "_is_sod_resource": True
                }
                self.resources.append(conflict_resource)
                self.resource_by_id[conflict_resource["id"]] = conflict_resource

                # Create grant
                grant = {
                    "id": self._generate_id("grant_"),
                    "employee_id": emp["id"],
                    "resource_id": conflict_resource["id"],
                    "granted_date": datetime.now().isoformat(),
                    "granted_by": "SYSTEM",
                    "grant_type": "Direct",
                    "justification": "Legacy access",
                    "_anomaly": f"sod_violation:{pattern[0]}+{pattern[1]}"
                }
                self.access_grants.append(grant)
                anomaly_count += 1

        # 4. Outlier access (access unusual for peer group)
        num_outliers = int(len(self.employees) * self.anomaly_config.outlier_access_percentage)
        outlier_employees = random.sample(self.employees, min(num_outliers, len(self.employees)))

        for emp in outlier_employees:
            # Give them access that's unusual for their level/team
            # Junior employee with Critical access
            if emp["job_level"] <= 2:
                critical_resources = [r for r in self.resources
                                    if r["sensitivity"] == "Critical"
                                    and not r.get("_is_sod_resource")]
                if critical_resources:
                    resource = random.choice(critical_resources)
                    grant = {
                        "id": self._generate_id("grant_"),
                        "employee_id": emp["id"],
                        "resource_id": resource["id"],
                        "granted_date": datetime.now().isoformat(),
                        "granted_by": emp.get("manager_id", "SYSTEM"),
                        "grant_type": "Direct",
                        "justification": "Special project requirement",
                        "_anomaly": "outlier_junior_critical"
                    }
                    self.access_grants.append(grant)
                    anomaly_count += 1

        logger.info(f"Seeded {anomaly_count} anomalies")

    def _generate_risk_signals(self) -> None:
        """Generate risk signals (from Sentinel-like system)."""
        logger.info("Generating risk signals...")

        signal_types = [
            ("impossible_travel", "High", 0.01),
            ("unusual_access_pattern", "Medium", 0.03),
            ("off_hours_access", "Low", 0.05),
            ("bulk_download", "High", 0.008),
            ("privilege_escalation_attempt", "Critical", 0.002),
            ("mfa_fatigue", "Medium", 0.01),
        ]

        for signal_type, severity, rate in signal_types:
            num_signals = int(len(self.employees) * rate)
            affected_employees = random.sample(self.employees, min(num_signals, len(self.employees)))

            for emp in affected_employees:
                emp_grants = [g for g in self.access_grants if g["employee_id"] == emp["id"]]
                affected_resources = [g["resource_id"] for g in random.sample(emp_grants, min(3, len(emp_grants)))]

                signal = {
                    "id": self._generate_id("risk_"),
                    "employee_id": emp["id"],
                    "signal_type": signal_type,
                    "severity": severity,
                    "timestamp": (datetime.now() - timedelta(days=random.randint(0, 90))).isoformat(),
                    "description": f"{signal_type.replace('_', ' ').title()} detected for user {emp['full_name']}",
                    "affected_resources": affected_resources,
                    "resolved": random.random() < 0.7,  # 70% resolved
                    "resolved_at": None
                }

                if signal["resolved"]:
                    signal["resolved_at"] = (
                        datetime.fromisoformat(signal["timestamp"]) +
                        timedelta(days=random.randint(1, 14))
                    ).isoformat()

                self.risk_signals.append(signal)

        logger.info(f"Generated {len(self.risk_signals)} risk signals")

    def _print_summary(self) -> None:
        """Print a summary of generated data."""
        print("\n" + "="*60)
        print("SYNTHETIC DATA GENERATION SUMMARY")
        print("="*60)
        print(f"Random Seed: {self.seed}")
        print(f"Company: {self.company['name']}")
        print("-"*60)
        print(f"Locations:       {len(self.locations):,}")
        print(f"LOBs:            {len(self.lobs):,}")
        print(f"Sub-LOBs:        {len(self.sub_lobs):,}")
        print(f"Teams:           {len(self.teams):,}")
        print(f"Cost Centers:    {len(self.cost_centers):,}")
        print(f"Employees:       {len(self.employees):,}")
        print(f"Systems:         {len(self.systems):,}")
        print(f"Resources:       {len(self.resources):,}")
        print(f"Access Grants:   {len(self.access_grants):,}")
        print(f"Activity Summaries: {len(self.activity_summaries):,}")
        print(f"Risk Signals:    {len(self.risk_signals):,}")
        print("-"*60)

        # Anomaly summary
        anomalies = [g for g in self.access_grants if g.get("_anomaly")]
        print(f"Seeded Anomalies: {len(anomalies):,}")

        # Breakdown
        anomaly_types = {}
        for g in anomalies:
            atype = g.get("_anomaly", "unknown").split(":")[0]
            anomaly_types[atype] = anomaly_types.get(atype, 0) + 1

        for atype, count in sorted(anomaly_types.items()):
            print(f"  - {atype}: {count:,}")

        print("="*60 + "\n")

    def save_to_sqlite(self, db_path: str) -> None:
        """Save all generated data to SQLite database."""
        logger.info(f"Saving data to SQLite: {db_path}")

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Remove existing database
        if os.path.exists(db_path):
            os.remove(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.executescript("""
            CREATE TABLE company (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                industry TEXT,
                created_at TEXT
            );

            CREATE TABLE locations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                region TEXT,
                country TEXT,
                timezone TEXT
            );

            CREATE TABLE lobs (
                id TEXT PRIMARY KEY,
                company_id TEXT,
                name TEXT NOT NULL,
                code TEXT,
                headcount_target INTEGER,
                FOREIGN KEY (company_id) REFERENCES company(id)
            );

            CREATE TABLE sub_lobs (
                id TEXT PRIMARY KEY,
                lob_id TEXT,
                name TEXT NOT NULL,
                code TEXT,
                FOREIGN KEY (lob_id) REFERENCES lobs(id)
            );

            CREATE TABLE cost_centers (
                id TEXT PRIMARY KEY,
                code TEXT,
                name TEXT,
                lob_id TEXT,
                FOREIGN KEY (lob_id) REFERENCES lobs(id)
            );

            CREATE TABLE teams (
                id TEXT PRIMARY KEY,
                sub_lob_id TEXT,
                lob_id TEXT,
                name TEXT NOT NULL,
                cost_center_id TEXT,
                FOREIGN KEY (sub_lob_id) REFERENCES sub_lobs(id),
                FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id)
            );

            CREATE TABLE employees (
                id TEXT PRIMARY KEY,
                employee_number TEXT UNIQUE,
                email TEXT,
                full_name TEXT,
                first_name TEXT,
                last_name TEXT,
                team_id TEXT,
                manager_id TEXT,
                location_id TEXT,
                cost_center_id TEXT,
                job_title TEXT,
                job_code TEXT,
                job_family TEXT,
                job_level INTEGER,
                employment_type TEXT,
                hire_date TEXT,
                role_start_date TEXT,
                status TEXT,
                FOREIGN KEY (team_id) REFERENCES teams(id),
                FOREIGN KEY (manager_id) REFERENCES employees(id),
                FOREIGN KEY (location_id) REFERENCES locations(id)
            );

            CREATE TABLE systems (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                criticality TEXT,
                owner_employee_id TEXT,
                description TEXT,
                resource_types TEXT,
                sensitivity_distribution TEXT,
                FOREIGN KEY (owner_employee_id) REFERENCES employees(id)
            );

            CREATE TABLE resources (
                id TEXT PRIMARY KEY,
                system_id TEXT,
                resource_type TEXT,
                name TEXT,
                external_id TEXT,
                description TEXT,
                sensitivity TEXT,
                grants_access_to TEXT,
                FOREIGN KEY (system_id) REFERENCES systems(id)
            );

            CREATE TABLE access_grants (
                id TEXT PRIMARY KEY,
                employee_id TEXT,
                resource_id TEXT,
                granted_date TEXT,
                granted_by TEXT,
                grant_type TEXT,
                justification TEXT,
                last_certified_date TEXT,
                last_certified_by TEXT,
                anomaly_type TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (resource_id) REFERENCES resources(id)
            );

            CREATE TABLE activity_summaries (
                id TEXT PRIMARY KEY,
                employee_id TEXT,
                resource_id TEXT,
                access_grant_id TEXT,
                total_access_count INTEGER,
                first_accessed TEXT,
                last_accessed TEXT,
                access_count_7d INTEGER,
                access_count_30d INTEGER,
                access_count_90d INTEGER,
                days_since_grant INTEGER,
                days_since_last_use INTEGER,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                FOREIGN KEY (access_grant_id) REFERENCES access_grants(id)
            );

            CREATE TABLE risk_signals (
                id TEXT PRIMARY KEY,
                employee_id TEXT,
                signal_type TEXT,
                severity TEXT,
                timestamp TEXT,
                description TEXT,
                affected_resources TEXT,
                resolved INTEGER,
                resolved_at TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );

            -- Create indices for common queries
            CREATE INDEX idx_employees_team ON employees(team_id);
            CREATE INDEX idx_employees_manager ON employees(manager_id);
            CREATE INDEX idx_employees_job_level ON employees(job_level);
            CREATE INDEX idx_access_grants_employee ON access_grants(employee_id);
            CREATE INDEX idx_access_grants_resource ON access_grants(resource_id);
            CREATE INDEX idx_resources_system ON resources(system_id);
            CREATE INDEX idx_resources_sensitivity ON resources(sensitivity);
            CREATE INDEX idx_activity_employee ON activity_summaries(employee_id);
            CREATE INDEX idx_activity_grant ON activity_summaries(access_grant_id);
            CREATE INDEX idx_risk_signals_employee ON risk_signals(employee_id);
        """)

        # Insert data
        cursor.execute(
            "INSERT INTO company VALUES (?, ?, ?, ?)",
            (self.company["id"], self.company["name"],
             self.company["industry"], self.company["created_at"])
        )

        for loc in self.locations:
            cursor.execute(
                "INSERT INTO locations VALUES (?, ?, ?, ?, ?)",
                (loc["id"], loc["name"], loc["region"], loc["country"], loc["timezone"])
            )

        for lob in self.lobs:
            cursor.execute(
                "INSERT INTO lobs VALUES (?, ?, ?, ?, ?)",
                (lob["id"], lob["company_id"], lob["name"], lob["code"], lob["headcount_target"])
            )

        for sub_lob in self.sub_lobs:
            cursor.execute(
                "INSERT INTO sub_lobs VALUES (?, ?, ?, ?)",
                (sub_lob["id"], sub_lob["lob_id"], sub_lob["name"], sub_lob["code"])
            )

        for cc in self.cost_centers:
            cursor.execute(
                "INSERT INTO cost_centers VALUES (?, ?, ?, ?)",
                (cc["id"], cc["code"], cc["name"], cc["lob_id"])
            )

        for team in self.teams:
            cursor.execute(
                "INSERT INTO teams VALUES (?, ?, ?, ?, ?)",
                (team["id"], team["sub_lob_id"], team["lob_id"],
                 team["name"], team.get("cost_center_id"))
            )

        for emp in self.employees:
            cursor.execute(
                """INSERT INTO employees VALUES
                   (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp["id"], emp["employee_number"], emp["email"], emp["full_name"],
                 emp["first_name"], emp["last_name"], emp["team_id"], emp["manager_id"],
                 emp["location_id"], emp["cost_center_id"], emp["job_title"],
                 emp["job_code"], emp["job_family"], emp["job_level"],
                 emp["employment_type"], emp["hire_date"], emp["role_start_date"],
                 emp["status"])
            )

        for sys in self.systems:
            cursor.execute(
                "INSERT INTO systems VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (sys["id"], sys["name"], sys["type"], sys["criticality"],
                 sys["owner_employee_id"], sys["description"],
                 json.dumps(sys["resource_types"]), json.dumps(sys["sensitivity_distribution"]))
            )

        for res in self.resources:
            cursor.execute(
                "INSERT INTO resources VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (res["id"], res["system_id"], res["resource_type"], res["name"],
                 res["external_id"], res["description"], res["sensitivity"],
                 json.dumps(res["grants_access_to"]))
            )

        for grant in self.access_grants:
            cursor.execute(
                "INSERT INTO access_grants VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (grant["id"], grant["employee_id"], grant["resource_id"],
                 grant["granted_date"], grant["granted_by"], grant["grant_type"],
                 grant["justification"], grant.get("last_certified_date"),
                 grant.get("last_certified_by"), grant.get("_anomaly"))
            )

        for summary in self.activity_summaries:
            cursor.execute(
                "INSERT INTO activity_summaries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (summary["id"], summary["employee_id"], summary["resource_id"],
                 summary["access_grant_id"], summary["total_access_count"],
                 summary["first_accessed"], summary["last_accessed"],
                 summary["access_count_7d"], summary["access_count_30d"],
                 summary["access_count_90d"], summary["days_since_grant"],
                 summary["days_since_last_use"])
            )

        for signal in self.risk_signals:
            cursor.execute(
                "INSERT INTO risk_signals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (signal["id"], signal["employee_id"], signal["signal_type"],
                 signal["severity"], signal["timestamp"], signal["description"],
                 json.dumps(signal["affected_resources"]), 1 if signal["resolved"] else 0,
                 signal["resolved_at"])
            )

        conn.commit()
        conn.close()

        logger.info(f"Data saved successfully to {db_path}")

    def save_to_json(self, output_dir: str) -> None:
        """Save all generated data to JSON files."""
        logger.info(f"Saving data to JSON: {output_dir}")

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        datasets = {
            "company": [self.company],
            "locations": self.locations,
            "lobs": self.lobs,
            "sub_lobs": self.sub_lobs,
            "cost_centers": self.cost_centers,
            "teams": self.teams,
            "employees": self.employees,
            "systems": self.systems,
            "resources": self.resources,
            "access_grants": self.access_grants,
            "activity_summaries": self.activity_summaries,
            "risk_signals": self.risk_signals
        }

        for name, data in datasets.items():
            filepath = os.path.join(output_dir, f"{name}.json")
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"  Saved {name}.json ({len(data):,} records)")

        # Save metadata
        metadata = {
            "seed": self.seed,
            "generated_at": datetime.now().isoformat(),
            "config": {
                "org": asdict(self.org_config),
                "access": asdict(self.access_config),
                "activity": asdict(self.activity_config),
                "anomaly": asdict(self.anomaly_config)
            },
            "record_counts": {name: len(data) for name, data in datasets.items()}
        }

        with open(os.path.join(output_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info("JSON export complete")


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic enterprise data for ARAS demo"
    )

    parser.add_argument(
        "--employees", "-n",
        type=int,
        default=10000,
        help="Number of employees to generate (default: 10000)"
    )

    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data",
        help="Output directory (default: data/)"
    )

    parser.add_argument(
        "--format", "-f",
        choices=["sqlite", "json", "both"],
        default="both",
        help="Output format (default: both)"
    )

    parser.add_argument(
        "--db-name",
        type=str,
        default="aras.db",
        help="SQLite database filename (default: aras.db)"
    )

    args = parser.parse_args()

    # Configure
    org_config = OrgConfig(total_employees=args.employees)

    # Generate
    generator = EnterpriseDataGenerator(
        org_config=org_config,
        seed=args.seed
    )

    generator.generate_all()

    # Save
    if args.format in ["sqlite", "both"]:
        db_path = os.path.join(args.output, args.db_name)
        generator.save_to_sqlite(db_path)

    if args.format in ["json", "both"]:
        json_dir = os.path.join(args.output, "json")
        generator.save_to_json(json_dir)

    print(f"\nData generation complete! Output saved to: {args.output}/")
    print(f"To regenerate the same data, use: --seed {generator.seed}")


if __name__ == "__main__":
    main()
