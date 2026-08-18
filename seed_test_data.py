from __future__ import annotations

import os
import re
import requests

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "http://127.0.0.1:8000"

ORGANIZATION_ID = 2


# ============================================================
# EXISTING DEPARTMENTS
#
# DO NOT CREATE THESE AGAIN.
# They already exist in the database.
# ============================================================

DEPARTMENTS = {
    "Finance": 1,
    "IT": 2,
    "Marketing": 3,
    "Research and Development": 10,
    "Cybersecurity": 11,
}


# ============================================================
# EXISTING TEAMS
#
# DO NOT CREATE THESE AGAIN.
# They already exist in the database.
# ============================================================

TEAMS = {
    # Finance
    ("Finance", "IPhone 18 Series"): 3,
    ("Finance", "Accounting"): 12,
    ("Finance", "Financial Planning"): 13,

    # IT
    ("IT", "Macbook Pro"): 4,
    ("IT", "Infrastructure"): 14,
    ("IT", "Technical Support"): 15,

    # Marketing
    (
        "Marketing",
        "Marketing team of Iphone 18 series",
    ): 5,
    ("Marketing", "Digital Marketing"): 16,
    ("Marketing", "Brand Strategy"): 17,

    # Research and Development
    (
        "Research and Development",
        "Artificial Intelligence",
    ): 18,
    (
        "Research and Development",
        "Machine Learning",
    ): 19,
    (
        "Research and Development",
        "Product Research",
    ): 20,

    # Cybersecurity
    (
        "Cybersecurity",
        "Application Security",
    ): 21,
    (
        "Cybersecurity",
        "Network Security",
    ): 22,
    (
        "Cybersecurity",
        "Security Operations",
    ): 23,
}


# ============================================================
# EXISTING EMPLOYEES
#
# These users are already in the database.
# They count toward the 5 employees required by their team.
# ============================================================

EXISTING_EMPLOYEES = {
    ("Finance", "IPhone 18 Series"): 1,
    ("IT", "Macbook Pro"): 1,
}


# ============================================================
# EMPLOYEE NAMES
#
# We need exactly 73 NEW employees:
#
# 15 teams × 5 employees = 75
# 75 - 2 existing = 73
# ============================================================

EMPLOYEE_NAMES = [
    "Abhishek Tajane",
    "Omraj",
    "Ravi Kishan",
    "Harsh Singh",
    "Aditya Kulkarni",
    "Rohan Mehta",
    "Aman Gupta",
    "Kunal Shah",
    "Vivek Joshi",
    "Arjun Nair",
    "Varun Rao",
    "Yash Thakur",
    "Siddharth Patil",
    "Rahul Verma",
    "Akash Sharma",
    "Sahil Khan",
    "Nikhil Jain",
    "Aniket More",
    "Prathamesh Patil",
    "Tejas Deshmukh",
    "Vedant Joshi",
    "Shubham Mishra",
    "Mohit Agarwal",
    "Ayush Singh",
    "Ritesh Kumar",
    "Rohit Yadav",
    "Manish Tiwari",
    "Abhinav Gupta",
    "Dhruv Shah",
    "Parth Mehta",
    "Ishan Kulkarni",
    "Tanmay Patil",
    "Atharva Joshi",
    "Saurabh More",
    "Akshay Desai",
    "Nilesh Pawar",
    "Pranav Shinde",
    "Chinmay Deshmukh",
    "Omkar Jadhav",
    "Harshad Patil",
    "Swapnil Joshi",
    "Mandar Kulkarni",
    "Karan Shah",
    "Raj Malhotra",
    "Dev Patel",
    "Vikram Singh",
    "Varun Sharma",
    "Rajat Gupta",
    "Ansh Verma",
    "Kabir Khan",
    "Aarav Mehta",
    "Vihaan Rao",
    "Reyansh Patel",
    "Aaryan Shah",
    "Krish Jain",
    "Rudra Singh",
    "Neil Nair",
    "Atharv Kulkarni",
    "Samar Patil",
    "Shreyas Joshi",
    "Manav Desai",
    "Rishabh Verma",
    "Mihir Shah",
    "Kartik More",
    "Soham Patil",
    "Yuvraj Singh",
    "Adit Jain",
    "Hrishikesh Rao",
    "Amol Deshmukh",
    "Vishal Patil",
    "Sameer Khan",
    "Deepak Sharma",
    "Nitin Verma",
    "Rakesh Gupta",
    "Sachin Joshi",
]


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()


# ============================================================
# AUTHENTICATION
# ============================================================

def setup_auth() -> None:

    token = os.getenv(
        "INTELLEX_ADMIN_TOKEN"
    )

    if not token:
        raise RuntimeError(
            "\nINTELLEX_ADMIN_TOKEN is not set.\n\n"
            "PowerShell:\n\n"
            '$env:INTELLEX_ADMIN_TOKEN="YOUR_TOKEN"\n'
            "python seed_test_data.py\n"
        )

    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    )

    print("Authentication token loaded.")


# ============================================================
# HTTP POST
# ============================================================

def post(
    endpoint: str,
    payload: dict,
) -> dict:

    url = f"{BASE_URL}{endpoint}"

    response = session.post(
        url,
        json=payload,
        timeout=30,
    )

    if not response.ok:

        print("\n" + "=" * 70)
        print("API REQUEST FAILED")
        print("=" * 70)

        print("URL:")
        print(url)

        print("\nStatus:")
        print(response.status_code)

        print("\nResponse:")
        print(response.text)

        print("\nPayload:")
        print(payload)

        print("=" * 70)

        response.raise_for_status()

    return response.json()


# ============================================================
# EMAIL / USERNAME
# ============================================================

def username_from_name(name: str) -> str:

    return re.sub(
        r"[^a-z0-9]",
        "",
        name.lower(),
    )


# ============================================================
# BUILD EMPLOYEE PLAN
# ============================================================

def build_employee_plan():

    print("\n" + "=" * 70)
    print("BUILDING EMPLOYEE PLAN")
    print("=" * 70)

    plan = []

    total_required = 0

    for (
        department_name,
        team_name,
    ) in TEAMS:

        existing_count = EXISTING_EMPLOYEES.get(
            (
                department_name,
                team_name,
            ),
            0,
        )

        required = 5 - existing_count

        if required < 0:

            raise RuntimeError(
                f"\nInvalid existing employee count:\n"
                f"{department_name} / {team_name}\n"
                f"Existing: {existing_count}\n"
                f"Target: 5"
            )

        plan.append(
            {
                "department": department_name,
                "team": team_name,
                "department_id": DEPARTMENTS[
                    department_name
                ],
                "team_id": TEAMS[
                    (
                        department_name,
                        team_name,
                    )
                ],
                "existing": existing_count,
                "required": required,
            }
        )

        total_required += required

        print(
            f"{department_name:<25}"
            f" | {team_name:<35}"
            f" | Existing: {existing_count}"
            f" | Create: {required}"
        )

    print("\n" + "-" * 70)

    print(
        f"Total new employees required: "
        f"{total_required}"
    )

    if total_required != 73:

        raise RuntimeError(
            f"\nExpected exactly 73 new employees "
            f"but calculated {total_required}."
        )

    if len(EMPLOYEE_NAMES) != 75:

        raise RuntimeError(
            f"\nEmployee name list must contain "
            f"75 names, found {len(EMPLOYEE_NAMES)}."
        )

    return plan


# ============================================================
# PRE-FLIGHT CHECK
#
# IMPORTANT:
# No POST requests happen before this function completes.
# ============================================================

def preflight(plan) -> None:

    print("\n" + "=" * 70)
    print("PRE-FLIGHT CHECK")
    print("=" * 70)

    # --------------------------------------------------------
    # Check departments
    # --------------------------------------------------------

    if len(DEPARTMENTS) != 5:

        raise RuntimeError(
            "Expected exactly 5 departments."
        )

    # --------------------------------------------------------
    # Check teams
    # --------------------------------------------------------

    if len(TEAMS) != 15:

        raise RuntimeError(
            "Expected exactly 15 teams."
        )

    # --------------------------------------------------------
    # Check every department has 3 teams
    # --------------------------------------------------------

    for department_name in DEPARTMENTS:

        count = sum(
            1
            for department, _ in TEAMS
            if department == department_name
        )

        if count != 3:

            raise RuntimeError(
                f"{department_name} has "
                f"{count} teams instead of 3."
            )

    # --------------------------------------------------------
    # Check employee names
    # --------------------------------------------------------

    if len(EMPLOYEE_NAMES) < 73:

        raise RuntimeError(
            "Not enough employee names."
        )

    # --------------------------------------------------------
    # Check generated usernames
    # --------------------------------------------------------

    usernames = []

    for name in EMPLOYEE_NAMES:

        username = username_from_name(name)

        if not username:

            raise RuntimeError(
                f"Invalid employee name: {name}"
            )

        usernames.append(username)

    # --------------------------------------------------------
    # Check duplicate usernames
    # --------------------------------------------------------

    if len(usernames) != len(set(usernames)):

        duplicates = {
            x
            for x in usernames
            if usernames.count(x) > 1
        }

        raise RuntimeError(
            f"Duplicate usernames found: "
            f"{duplicates}"
        )

    # --------------------------------------------------------
    # Check expected existing employees
    # --------------------------------------------------------

    expected_existing = {
        (
            "Finance",
            "IPhone 18 Series",
        ): 1,

        (
            "IT",
            "Macbook Pro",
        ): 1,
    }

    if EXISTING_EMPLOYEES != expected_existing:

        raise RuntimeError(
            "Existing employee configuration "
            "does not match expected database state."
        )

    # --------------------------------------------------------
    # Final check
    # --------------------------------------------------------

    total_existing = sum(
        EXISTING_EMPLOYEES.values()
    )

    total_new = sum(
        item["required"]
        for item in plan
    )

    total_final = (
        total_existing +
        total_new
    )

    if total_final != 75:

        raise RuntimeError(
            f"Expected 75 total employees, "
            f"calculated {total_final}."
        )

    print("✓ 5 departments")
    print("✓ 15 teams")
    print("✓ 3 teams per department")
    print("✓ 2 existing employees accounted for")
    print("✓ 73 new employees required")
    print("✓ 75 employees after seeding")
    print("✓ No ORG_ADMIN users will be created")
    print("✓ No departments will be created")
    print("✓ No teams will be created")
    print("✓ Employee usernames are unique")

    print("\nPRE-FLIGHT PASSED.")


# ============================================================
# CREATE EMPLOYEES
# ============================================================

def create_employees(plan) -> None:

    print("\n" + "=" * 70)
    print("CREATING EMPLOYEES")
    print("=" * 70)

    name_index = 0
    created_count = 0

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # We use the first 73 names.
    #
    # 75 total target employees
    # - 2 existing
    # = 73 new
    # --------------------------------------------------------

    names_to_use = EMPLOYEE_NAMES[:73]

    for item in plan:

        department_name = item["department"]
        team_name = item["team"]

        department_id = item["department_id"]
        team_id = item["team_id"]

        required = item["required"]

        print("\n" + "-" * 70)

        print(
            f"{department_name} -> {team_name}"
        )

        print(
            f"Existing: {item['existing']}"
        )

        print(
            f"Creating: {required}"
        )

        for _ in range(required):

            name = names_to_use[name_index]

            name_index += 1

            username = username_from_name(name)

            email = (
                f"{username}@gmail.com"
            )

            password = username

            payload = {
                "name": name,
                "email": email,
                "password": password,
                "department_id": department_id,
                "team_id": team_id,
            }

            print(
                f"  Creating "
                f"{name:<25}"
                f"| {email:<40}"
                f"| team_id={team_id}"
            )

            response = post(
                "/users/employees",
                payload,
            )

            user_id = (
                response.get("user_id")
                or response.get("id")
            )

            print(
                f"  ✓ Created user_id={user_id}"
            )

            created_count += 1

    # --------------------------------------------------------
    # Final local verification
    # --------------------------------------------------------

    if created_count != 73:

        raise RuntimeError(
            f"Expected to create 73 employees "
            f"but created {created_count}."
        )

    print("\n" + "=" * 70)

    print(
        f"SUCCESS: Created {created_count} employees."
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("\n" + "=" * 70)
    print("INTELLEX EMPLOYEE SEEDER")
    print("=" * 70)

    print(
        "\nOrganization:"
        " Apple"
        f" (organization_id={ORGANIZATION_ID})"
    )

    print(
        "\nIMPORTANT:"
        "\nThis script will NOT create departments."
        "\nThis script will NOT create teams."
        "\nThis script will NOT create ORG_ADMIN users."
        "\nIt only creates the missing EMPLOYEE users."
    )

    print(
        "\nPassword rule:"
        "\nemail username = password"
        "\n"
        "\nomraj@gmail.com -> omraj"
        "\nravikishan@gmail.com -> ravikishan"
        "\nharshsingh@gmail.com -> harshsingh"
    )

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    setup_auth()

    # --------------------------------------------------------
    # Build complete plan
    # --------------------------------------------------------

    plan = build_employee_plan()

    # --------------------------------------------------------
    # PRE-FLIGHT
    #
    # NO DATABASE CREATION HAPPENS BEFORE THIS.
    # --------------------------------------------------------

    preflight(plan)

    # --------------------------------------------------------
    # Ask for confirmation
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    print(
        "READY TO CREATE 73 EMPLOYEES"
    )

    print(
        "\nExisting data will NOT be modified."
    )

    print(
        "\nType YES to continue:"
    )

    confirmation = input(
        "> "
    ).strip()

    if confirmation != "YES":

        print(
            "\nCancelled."
            "\nNo employee records were created."
        )

        return

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    create_employees(plan)

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("SEEDING COMPLETE")
    print("=" * 70)

    print(
        "\nFinal target:"
        "\n  Departments : 5"
        "\n  Teams       : 15"
        "\n  Employees   : 75"
        "\n  ORG_ADMIN   : 0 created"
    )

    print(
        "\nExisting employees preserved:"
        "\n  Sagar Rajput"
        "\n  akashsingh"
    )


if __name__ == "__main__":
    main()