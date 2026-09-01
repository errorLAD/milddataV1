import os

SLUG_ALIASES = {
    "udhaar": "b2b-payment",
    "payment-reminder": "b2b-payment",
    "job-card": "machine-os",
    "machineos": "machine-os",
    "fleet": "fleet-management",
    "property": "property-management",
    "propflow": "property-management",
}

SAAS_PRODUCTS = {
    "b2b-payment": {
        "slug": "b2b-payment",
        "name": "Payment Reminder / B2B Payment",
        "folder_name": "b2bpayment",
        "project_name": "udhaar_crm",
        "category": "Finance & Payments",
        "category_code": "saas_tool",
        "developer": "Milda Data",
        "launch_date": "March 2025",
        "support_info": "Email, Chat, Ticket",
        "description": "B2B payment collections, automated payment reminders, customer ledgers, and invoice management platform.",
        "short_description": "Automate B2B payment reminders, track customer ledgers, and collect outstanding dues 3x faster.",
        "status": "active",
        "price_inr_monthly": 199.00,
        "price_inr_yearly": 1982.00,
        "price_usd_monthly": 5.00,
        "price_usd_yearly": 49.80,
        "env_var": "B2BPAYMENT_APP_URL",
        "default_url": "http://localhost:8001",
        "app_route": "/",
        "login_route": "/accounts/login/",
        "guest_route": "/accounts/guest-login/",
        "features": [
            {"title": "Automated WhatsApp & Email Reminders", "desc": "Send scheduled automated reminders to customers before and on due dates."},
            {"title": "Customer Ledger Management", "desc": "Maintain detailed real-time ledgers for every buyer and supplier balance."},
            {"title": "Invoice & Receipt Generation", "desc": "Issue GST-compliant invoices and automatic payment confirmation receipts."},
            {"title": "Collection Analytics Dashboard", "desc": "Real-time visibility into total receivables, overdue buckets, and DSO metrics."},
            {"title": "Multi-User Sales Agent Access", "desc": "Empower collection agents with mobile-ready ledger views and field logs."},
            {"title": "Role-Based Access Control", "desc": "Granular permissions for finance admins, accountants, and sales reps."},
        ],
        "dashboard_stats": {
            "stat1_label": "Total Receivables", "stat1_val": "₹4,85,000",
            "stat2_label": "Active Customers", "stat2_val": "142",
            "stat3_label": "Collected This Month", "stat3_val": "₹3,20,000",
            "stat4_label": "On-Time Ratio", "stat4_val": "94.5%",
        },
        "benefits": [
            "Reduce Day Sales Outstanding (DSO) by 45%",
            "Automate manual follow-up calls and messages",
            "Zero ledger errors with automated payment logs",
            "Cloud-based secure data backup & access from anywhere",
            "Built for enterprise B2B distributors and suppliers",
        ],
    },
    "supplier-onboarding": {
        "slug": "supplier-onboarding",
        "name": "Supplier Onboarding OS",
        "folder_name": "SupplierOnboarding",
        "project_name": "supplieros",
        "category": "Operations & Compliance",
        "category_code": "saas_tool",
        "developer": "Milda Data",
        "launch_date": "April 2025",
        "support_info": "Email, Chat, Ticket",
        "description": "Streamlined vendor onboarding, compliance verification, document collection, and approval workflows.",
        "short_description": "Digitize supplier registration, verify compliance documents, and automate multi-stage vendor approvals.",
        "status": "active",
        "price_inr_monthly": 199.00,
        "price_inr_yearly": 1982.00,
        "price_usd_monthly": 5.00,
        "price_usd_yearly": 49.80,
        "env_var": "SUPPLIER_ONBOARDING_APP_URL",
        "default_url": "http://localhost:8002",
        "app_route": "/",
        "login_route": "/login/",
        "guest_route": "/guest-login/",
        "features": [
            {"title": "Self-Service Supplier Portal", "desc": "Allow new vendors to upload GST, PAN, and banking documents directly."},
            {"title": "Automated Compliance Audits", "desc": "Verify document validity and set automatic expiry renewal alerts."},
            {"title": "Multi-Stage Approval Workflows", "desc": "Route applications automatically through Procurement, Legal, and Finance."},
            {"title": "Vendor Performance Scorecards", "desc": "Rate supplier delivery times, quality compliance, and fulfillment accuracy."},
            {"title": "Document Vault & Encryption", "desc": "Centralized 256-bit encrypted storage for contracts and certificates."},
            {"title": "Supplier Communication Log", "desc": "Audit trail of all email notifications, status updates, and compliance notes."},
        ],
        "dashboard_stats": {
            "stat1_label": "Active Suppliers", "stat1_val": "54",
            "stat2_label": "Pending Approvals", "stat2_val": "6",
            "stat3_label": "Verified Documents", "stat3_val": "312",
            "stat4_label": "Compliance Clearance", "stat4_val": "98.2%",
        },
        "benefits": [
            "Cut vendor onboarding time from weeks to 48 hours",
            "Eliminate compliance risks with automated document checks",
            "Transparent multi-department approval tracking",
            "Centralized document repository accessible anywhere",
            "Seamless integration with enterprise ERP systems",
        ],
    },
    "business-saas": {
        "slug": "business-saas",
        "name": "Business SaaS Lite",
        "folder_name": "buinessslite",
        "project_name": "businesslite_proj",
        "category": "ERP & Business",
        "category_code": "saas_tool",
        "developer": "Milda Data",
        "launch_date": "January 2025",
        "support_info": "Email, Chat, Ticket",
        "description": "Integrated core business management system covering sales, finance, inventory, purchasing, and reporting.",
        "short_description": "All-in-one business management for quotes, invoices, stock, employee operations, and P&L analytics.",
        "status": "active",
        "price_inr_monthly": 199.00,
        "price_inr_yearly": 1982.00,
        "price_usd_monthly": 5.00,
        "price_usd_yearly": 49.80,
        "env_var": "BUSINESSLITE_APP_URL",
        "default_url": "http://localhost:8003",
        "app_route": "/",
        "login_route": "/login/",
        "guest_route": "/guest-login/",
        "features": [
            {"title": "Sales & Purchase Management", "desc": "Create quotes, purchase orders, sales invoices, and customer receipts."},
            {"title": "Real-Time Stock Inventory", "desc": "Track multi-warehouse inventory levels, reorder points, and valuation."},
            {"title": "Financial P&L Statements", "desc": "Automatic profit and loss generation, expense tracking, and tax summaries."},
            {"title": "Employee & Payroll Operations", "desc": "Manage staff records, attendance logs, department roles, and salary slips."},
            {"title": "Custom Business Reports", "desc": "Export PDF and Excel reports for executive analysis and compliance."},
            {"title": "Role-Based Access Control", "desc": "Separate permissions for managers, accountants, sales, and warehouse staff."},
        ],
        "dashboard_stats": {
            "stat1_label": "Monthly Revenue", "stat1_val": "₹8,40,000",
            "stat2_label": "Active Quotes", "stat2_val": "28",
            "stat3_label": "Stock Items", "stat3_val": "1,450",
            "stat4_label": "Net Profit Margin", "stat4_val": "22.4%",
        },
        "benefits": [
            "Replace fragmented tools with a single unified ERP platform",
            "Instant visibility into company profits and expenses",
            "Automated stock level alerts to prevent out-of-stock orders",
            "Secure cloud accessibility for multi-branch operations",
        ],
    },
    "fleet-management": {
        "slug": "fleet-management",
        "name": "Fleet Management OS",
        "folder_name": "fleetmangment",
        "project_name": "config",
        "category": "Logistics & Transport",
        "category_code": "saas_tool",
        "developer": "Milda Data",
        "launch_date": "February 2025",
        "support_info": "Email, Chat, Ticket",
        "description": "Real-time vehicle tracking, trip playback, geofencing, driver PWA, maintenance scheduling, and fuel logs.",
        "short_description": "Live GPS vehicle tracking, driver PWA apps, trip analytics, fuel logging, and preventative maintenance.",
        "status": "active",
        "price_inr_monthly": 199.00,
        "price_inr_yearly": 1982.00,
        "price_usd_monthly": 5.00,
        "price_usd_yearly": 49.80,
        "env_var": "FLEET_MANAGEMENT_APP_URL",
        "default_url": "http://localhost:8004",
        "app_route": "/",
        "login_route": "/login/",
        "guest_route": "/guest-login/",
        "features": [
            {"title": "Live GPS Vehicle Tracking", "desc": "Real-time map tracking with speed alerts, route history, and playback."},
            {"title": "Driver Mobile PWA", "desc": "PWA app for drivers to log trip start/end, fuel purchases, and inspection notes."},
            {"title": "Geofence Boundary Alerts", "desc": "Define custom geofences and receive instant notifications on entry/exit."},
            {"title": "Preventative Maintenance Schedule", "desc": "Automate service alerts based on mileage and operating engine hours."},
            {"title": "Fuel Consumption Analytics", "desc": "Detect fuel theft, track mileage efficiency, and log fuel receipts."},
            {"title": "Trip & Operational Reports", "desc": "Generate detailed trip logs, driver performance scores, and idle time stats."},
        ],
        "dashboard_stats": {
            "stat1_label": "Active Vehicles", "stat1_val": "18",
            "stat2_label": "Assigned Drivers", "stat2_val": "24",
            "stat3_label": "Distance Today", "stat3_val": "1,420 km",
            "stat4_label": "Fleet Uptime", "stat4_val": "99.1%",
        },
        "benefits": [
            "Reduce fuel wastage and unnecessary engine idling by 30%",
            "Improve delivery speed with real-time route optimization",
            "Prevent breakdowns using automated preventative maintenance",
            "Seamless driver PWA accessibility without app store installation",
        ],
    },
    "stockflow": {
        "slug": "stockflow",
        "name": "StockFlow — Inventory & Purchasing",
        "folder_name": "Inventory + Purchasing",
        "project_name": "stockflow",
        "category": "Inventory & Supply Chain",
        "category_code": "saas_tool",
        "developer": "Milda Data",
        "launch_date": "January 2025",
        "support_info": "Email, Chat, Ticket",
        "description": "Stock management, purchasing automation, inventory valuation, multi-warehouse control, and financial reporting.",
        "short_description": "Control inventory across multiple warehouses, automate purchase orders, and track stock valuation.",
        "status": "active",
        "price_inr_monthly": 199.00,
        "price_inr_yearly": 1982.00,
        "price_usd_monthly": 5.00,
        "price_usd_yearly": 49.80,
        "env_var": "STOCKFLOW_APP_URL",
        "default_url": "http://localhost:8005",
        "app_route": "/",
        "login_route": "/accounts/login/",
        "guest_route": "/accounts/guest-login/",
        "features": [
            {"title": "Multi-Warehouse Management", "desc": "Track stock levels, transfers, and locations across multiple warehouses."},
            {"title": "Automated Purchase Orders", "desc": "Auto-generate POs when stock levels breach defined reorder thresholds."},
            {"title": "Goods Receipt Note (GRN)", "desc": "Log incoming shipments, verify vendor quantities, and record batch numbers."},
            {"title": "Inventory Valuation (FIFO/WAV)", "desc": "Calculate real-time stock valuation for balance sheet compliance."},
            {"title": "Barcode & SKU Scanning", "desc": "Fast stock check-in and dispatch scanning with barcode support."},
            {"title": "Stock Movement Audit Trail", "desc": "Complete history of stock receipts, transfers, adjustments, and sales."},
        ],
        "dashboard_stats": {
            "stat1_label": "Warehouses", "stat1_val": "6",
            "stat2_label": "Total SKUs", "stat2_val": "1,240",
            "stat3_label": "Stock Valuation", "stat3_val": "₹12,40,000",
            "stat4_label": "Reorder Alerts", "stat4_val": "3 Pending",
        },
        "benefits": [
            "Eliminate stockouts with automated reorder alerts",
            "Full visibility across multiple warehouse locations",
            "Accurate financial stock valuation compliant with accounting standards",
            "Streamline purchasing and vendor goods receipt verification",
        ],
    },
    "machine-os": {
        "slug": "machine-os",
        "name": "MachineOS",
        "folder_name": "machinelite",
        "project_name": "machine_os",
        "category": "Heavy Equipment & Machinery",
        "category_code": "saas_tool",
        "developer": "Milda Data",
        "launch_date": "February 2025",
        "support_info": "Email, Chat, Ticket",
        "description": "Heavy machinery fleet operations, operator logs, rental management, maintenance alerts, and trip tracking.",
        "short_description": "Manage heavy equipment fleets, operator hour logs, rental contracts, maintenance alerts, and fuel usage.",
        "status": "active",
        "price_inr_monthly": 199.00,
        "price_inr_yearly": 1982.00,
        "price_usd_monthly": 5.00,
        "price_usd_yearly": 49.80,
        "env_var": "MACHINE_OS_APP_URL",
        "default_url": "http://localhost:8006",
        "app_route": "/",
        "login_route": "/login/",
        "guest_route": "/guest-login/",
        "features": [
            {"title": "Equipment Health & Hour Logs", "desc": "Track engine operating hours, hydraulic status, and machine health."},
            {"title": "Operator Timesheets & Assignments", "desc": "Assign certified operators and log daily machine usage shifts."},
            {"title": "Machinery Rental Management", "desc": "Track client rental contracts, hourly billing rates, and dispatch status."},
            {"title": "Maintenance & Repair Alerts", "desc": "Schedule routine servicing based on engine hours and component wear."},
            {"title": "Fuel & Tank Monitoring", "desc": "Log diesel refills, monitor consumption per hour, and detect fuel anomalies."},
            {"title": "Project & Site Analytics", "desc": "Analyze machine utilization per construction site or mining project."},
        ],
        "dashboard_stats": {
            "stat1_label": "Heavy Machines", "stat1_val": "14",
            "stat2_label": "Active Rentals", "stat2_val": "9",
            "stat3_label": "Engine Hours Today", "stat3_val": "112 hrs",
            "stat4_label": "Machine Health", "stat4_val": "97.8%",
        },
        "benefits": [
            "Maximize heavy machine utilization and rental profitability",
            "Prevent catastrophic equipment failures with automated hour alerts",
            "Accurate hourly billing logs for rental customers",
            "Track diesel consumption and eliminate fuel loss",
        ],
    },
    "property-management": {
        "slug": "property-management",
        "name": "PropFlow — Property Management",
        "folder_name": "propertylite",
        "project_name": "propflow_proj",
        "category": "Real Estate & Leasing",
        "category_code": "saas_tool",
        "developer": "Milda Data",
        "launch_date": "May 2025",
        "support_info": "Email, Chat, Ticket",
        "description": "Property portfolio tracking, tenant leases, automated rent collection, maintenance requests, and financial reports.",
        "short_description": "Simplify property operations, manage tenants, collect rent on time, and grow your real estate business with ease.",
        "status": "active",
        "price_inr_monthly": 199.00,
        "price_inr_yearly": 1982.00,
        "price_usd_monthly": 5.00,
        "price_usd_yearly": 49.80,
        "env_var": "PROPERTYLITE_APP_URL",
        "default_url": "http://localhost:8007",
        "app_route": "/",
        "login_route": "/login/",
        "guest_route": "/guest-login/",
        "features": [
            {"title": "Property Portfolio Management", "desc": "Manage all your properties, units, and ownership details in one place."},
            {"title": "Tenant & Lease Tracking", "desc": "Track tenants, lease agreements, security deposits, and renewal dates."},
            {"title": "Automated Rent Collection", "desc": "Automate rent collection, send reminders, and track incoming payments."},
            {"title": "Maintenance Request Portal", "desc": "Tenants can raise maintenance requests and track repair status in real time."},
            {"title": "Expenses & Bills Management", "desc": "Track property expenses, vendor bills, utility costs, and net revenue."},
            {"title": "Reports & Financial Analytics", "desc": "Get real-time insights into occupancy rates, rental yields, and cash flow."},
            {"title": "Role-Based Access Control", "desc": "Granular permissions for property owners, managers, and tenants."},
            {"title": "Enterprise Data Security", "desc": "256-bit encryption for lease contracts and tenant documents."},
            {"title": "Automated Notifications", "desc": "SMS & email alerts for upcoming rent due dates and lease expirations."},
            {"title": "Document Vault", "desc": "Centralized file storage for lease agreements, ID proofs, and receipts."},
        ],
        "dashboard_stats": {
            "stat1_label": "Properties", "stat1_val": "24",
            "stat2_label": "Tenants", "stat2_val": "48",
            "stat3_label": "Rent Collected", "stat3_val": "₹2,45,000",
            "stat4_label": "Occupancy Rate", "stat4_val": "92%",
        },
        "benefits": [
            "Easy to use and quick to set up in 5 minutes",
            "Automated rent reminders eliminate overdue payments",
            "Secure, 256-bit encrypted cloud platform accessible anywhere",
            "Access from desktop, tablet, and mobile devices",
            "Regular feature updates and dedicated email & chat support",
            "Tailored specifically for Indian and international real estate markets",
        ],
    },
}


def get_saas_product(slug):
    """Retrieve SaaS product configuration by slug or canonical alias."""
    target_slug = SLUG_ALIASES.get(slug.lower(), slug)
    return SAAS_PRODUCTS.get(target_slug)


def get_all_saas_products(category=None, include_coming_soon=True, currency="INR", billing_cycle="monthly"):
    """Return list of all configured SaaS products with active region and billing cycle pricing."""
    products = []
    cycle = billing_cycle.lower() if billing_cycle in ("monthly", "yearly") else "monthly"
    curr = currency.upper() if currency in ("INR", "USD") else "INR"

    for item in SAAS_PRODUCTS.values():
        p = item.copy()
        p["price_inr_monthly_str"] = "₹199/mo"
        p["price_inr_yearly_str"] = "₹1,982/yr (Save 17%)"
        p["price_usd_monthly_str"] = "$5/mo"
        p["price_usd_yearly_str"] = "$49.80/yr (Save 17%)"

        if curr == "USD":
            if cycle == "yearly":
                p["display_price"] = "$49.80/yr (Save 17%)"
                p["price_amount"] = 49.80
            else:
                p["display_price"] = "$5/mo"
                p["price_amount"] = 5.00
            p["currency_symbol"] = "$"
        else:
            if cycle == "yearly":
                p["display_price"] = "₹1,982/yr (Save 17%)"
                p["price_amount"] = 1982.00
            else:
                p["display_price"] = "₹199/mo"
                p["price_amount"] = 199.00
            p["currency_symbol"] = "₹"

        products.append(p)

    if category:
        products = [p for p in products if p["category_code"] == category or p["category"].lower() == category.lower()]
    if not include_coming_soon:
        products = [p for p in products if p.get("status") != "coming_soon"]
    return products


def resolve_saas_url(slug, route_type="guest"):
    """
    Safely resolve the target URL for a registered SaaS product.
    Supports route_type="app", "login", or "guest".
    Returns full target URL string or None if unconfigured.
    """
    product = get_saas_product(slug)
    if not product:
        return None

    base_url = os.environ.get(product["env_var"], product["default_url"]).rstrip("/")
    if route_type == "login":
        sub_path = product.get("login_route", "/login/")
    elif route_type == "guest":
        sub_path = product.get("guest_route", product.get("app_route", "/"))
    else:
        sub_path = product.get("app_route", "/")
    
    if not sub_path.startswith("/"):
        sub_path = "/" + sub_path

    return f"{base_url}{sub_path}"
