"""
Generate clean, authentic technical SVG placeholders and logos for GROWTECH ENGINEERS.
Complies with requirement: Clearly identified temporary placeholders where actual assets are unavailable.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'static', 'images')
FACTORY_DIR = os.path.join(IMG_DIR, 'factory')
PRODUCTS_DIR = os.path.join(IMG_DIR, 'products')
CUSTOMERS_DIR = os.path.join(IMG_DIR, 'customers')

os.makedirs(FACTORY_DIR, exist_ok=True)
os.makedirs(PRODUCTS_DIR, exist_ok=True)
os.makedirs(CUSTOMERS_DIR, exist_ok=True)

# 1. Company Logo SVG
logo_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 80" width="100%" height="100%">
  <defs>
    <linearGradient id="gearBlue" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0b3866" />
      <stop offset="100%" stop-color="#125291" />
    </linearGradient>
    <linearGradient id="gearGreen" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#198754" />
      <stop offset="100%" stop-color="#28a745" />
    </linearGradient>
  </defs>
  
  <!-- Industrial Emblem / Precision Gear Icon -->
  <g transform="translate(10, 8)">
    <!-- Base shield / precision block -->
    <rect x="2" y="2" width="60" height="60" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" />
    
    <!-- Outer Gear teeth -->
    <path d="M32 6 L36 6 L37 11 L41 12.5 L45 9 L48 12 L45.5 16 L47 20 L52 21 L52 25 L47 26 L45.5 30 L48 34 L45 37 L41 33.5 L37 35 L36 40 L32 40 L31 35 L27 33.5 L23 37 L20 34 L22.5 30 L21 26 L16 25 L16 21 L21 20 L22.5 16 L20 12 L23 9 L27 12.5 L31 11 Z" fill="url(#gearBlue)" />
    
    <!-- Inner precision ring -->
    <circle cx="34" cy="23" r="10" fill="#ffffff" stroke="#198754" stroke-width="2.5" />
    
    <!-- Precision Crosshair / Center hub -->
    <circle cx="34" cy="23" r="4.5" fill="#198754" />
    <line x1="34" y1="10" x2="34" y2="36" stroke="#0b3866" stroke-width="1" stroke-dasharray="2,2" opacity="0.6" />
    <line x1="21" y1="23" x2="47" y2="23" stroke="#0b3866" stroke-width="1" stroke-dasharray="2,2" opacity="0.6" />
    
    <!-- Growth chevron in green -->
    <polyline points="22,50 32,42 42,50" fill="none" stroke="#198754" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
    <polyline points="26,56 32,50 38,56" fill="none" stroke="#0b3866" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
  </g>
  
  <!-- Brand Text -->
  <g transform="translate(82, 16)">
    <text x="0" y="25" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="25" font-weight="800" letter-spacing="1" fill="#0b3866">GROWTECH</text>
    <text x="144" y="25" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="25" font-weight="700" letter-spacing="1" fill="#198754">ENGINEERS</text>
    <line x1="0" y1="33" x2="310" y2="33" stroke="#0b3866" stroke-width="2" />
    <line x1="0" y1="36" x2="160" y2="36" stroke="#198754" stroke-width="1.5" />
    <text x="0" y="49" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="9.5" font-weight="600" letter-spacing="1.2" fill="#556980">TOOLING • JIGS &amp; FIXTURES • PRECISION DIES • MANESAR</text>
  </g>
</svg>'''

with open(os.path.join(IMG_DIR, 'logo.svg'), 'w', encoding='utf-8') as f:
    f.write(logo_svg)

# Helper function to generate clean technical blueprint / industrial placeholders
def create_technical_placeholder(path, title, subtitle, category_code, icon_type='tool'):
    width = 800
    height = 520
    
    # Custom icon paths based on icon_type
    icon_content = ''
    if icon_type == 'jig':
        icon_content = '''
        <!-- Clamping / Fixture Symbol -->
        <rect x="360" y="160" width="80" height="70" fill="#e2e8f0" stroke="#0b3866" stroke-width="3" rx="4"/>
        <line x1="330" y1="195" x2="360" y2="195" stroke="#198754" stroke-width="4" stroke-linecap="round"/>
        <line x1="440" y1="195" x2="470" y2="195" stroke="#198754" stroke-width="4" stroke-linecap="round"/>
        <circle cx="400" cy="195" r="16" fill="#0b3866"/>
        <circle cx="400" cy="195" r="7" fill="#ffffff"/>
        <rect x="340" y="250" width="120" height="20" fill="#0b3866" rx="3"/>
        <line x1="360" y1="230" x2="360" y2="250" stroke="#64748b" stroke-width="4"/>
        <line x1="440" y1="230" x2="440" y2="250" stroke="#64748b" stroke-width="4"/>
        '''
    elif icon_type == 'gauge':
        icon_content = '''
        <!-- Dial Indicator / Gauge Symbol -->
        <circle cx="400" cy="190" r="45" fill="#f8fafc" stroke="#0b3866" stroke-width="4"/>
        <circle cx="400" cy="190" r="38" fill="none" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="3,3"/>
        <circle cx="400" cy="190" r="5" fill="#198754"/>
        <line x1="400" y1="190" x2="422" y2="168" stroke="#dc3545" stroke-width="2.5" stroke-linecap="round"/>
        <rect x="395" y="235" width="10" height="35" fill="#64748b" stroke="#0b3866" stroke-width="2"/>
        <polygon points="393,270 407,270 400,285" fill="#0b3866"/>
        '''
    elif icon_type == 'press':
        icon_content = '''
        <!-- Press Tool / Stamping Machine -->
        <rect x="340" y="140" width="120" height="25" fill="#0b3866" rx="2"/>
        <rect x="340" y="265" width="120" height="25" fill="#0b3866" rx="2"/>
        <rect x="350" y="165" width="16" height="100" fill="#94a3b8" stroke="#475569" stroke-width="1"/>
        <rect x="434" y="165" width="16" height="100" fill="#94a3b8" stroke="#475569" stroke-width="1"/>
        <!-- Ram -->
        <rect x="375" y="175" width="50" height="35" fill="#198754" rx="2"/>
        <path d="M385 210 L415 210 L400 230 Z" fill="#0b3866"/>
        '''
    elif icon_type == 'rack':
        icon_content = '''
        <!-- Trolley / Storage Racks -->
        <line x1="330" y1="150" x2="470" y2="150" stroke="#0b3866" stroke-width="4"/>
        <line x1="330" y1="195" x2="470" y2="195" stroke="#0b3866" stroke-width="4"/>
        <line x1="330" y1="240" x2="470" y2="240" stroke="#0b3866" stroke-width="4"/>
        <line x1="340" y1="140" x2="340" y2="260" stroke="#0b3866" stroke-width="4"/>
        <line x1="460" y1="140" x2="460" y2="260" stroke="#0b3866" stroke-width="4"/>
        <!-- Wheels -->
        <circle cx="340" cy="272" r="10" fill="#198754" stroke="#0b3866" stroke-width="2"/>
        <circle cx="460" cy="272" r="10" fill="#198754" stroke="#0b3866" stroke-width="2"/>
        '''
    elif icon_type == 'engineering':
        icon_content = '''
        <!-- Engineering Compass / CAD Grid -->
        <circle cx="400" cy="180" r="40" fill="none" stroke="#0b3866" stroke-width="3"/>
        <line x1="400" y1="130" x2="400" y2="230" stroke="#198754" stroke-width="2" stroke-dasharray="4,3"/>
        <line x1="350" y1="180" x2="450" y2="180" stroke="#198754" stroke-width="2" stroke-dasharray="4,3"/>
        <polygon points="400,145 425,225 375,225" fill="none" stroke="#0b3866" stroke-width="3"/>
        <circle cx="400" cy="145" r="5" fill="#dc3545"/>
        '''
    else:
        # Factory / Infrastructure
        icon_content = '''
        <!-- Industrial Facility / Machinery -->
        <polygon points="330,240 330,170 370,195 370,170 410,195 410,170 470,205 470,240" fill="#0b3866"/>
        <rect x="330" y="240" width="140" height="25" fill="#334155"/>
        <rect x="350" y="215" width="18" height="22" fill="#38bdf8"/>
        <rect x="385" y="215" width="18" height="22" fill="#38bdf8"/>
        <rect x="430" y="215" width="22" height="25" fill="#198754"/>
        <line x1="330" y1="265" x2="470" y2="265" stroke="#198754" stroke-width="4"/>
        '''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <defs>
    <pattern id="gridPattern" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e2e8f0" stroke-width="1"/>
    </pattern>
    <pattern id="dotPattern" width="20" height="20" patternUnits="userSpaceOnUse">
      <circle cx="10" cy="10" r="1" fill="#cbd5e1" />
    </pattern>
  </defs>

  <!-- Technical Background -->
  <rect width="{width}" height="{height}" fill="#f8fafc"/>
  <rect width="{width}" height="{height}" fill="url(#gridPattern)"/>
  <rect width="{width}" height="{height}" fill="url(#dotPattern)" opacity="0.6"/>

  <!-- Industrial Framing -->
  <rect x="16" y="16" width="{width - 32}" height="{height - 32}" fill="none" stroke="#0b3866" stroke-width="2" stroke-opacity="0.3"/>
  <rect x="24" y="24" width="{width - 48}" height="{height - 48}" fill="none" stroke="#198754" stroke-width="1" stroke-opacity="0.3"/>

  <!-- Corner Alignment Crosshairs -->
  <g stroke="#0b3866" stroke-width="1.5">
    <line x1="12" y1="16" x2="26" y2="16"/>
    <line x1="16" y1="12" x2="16" y2="26"/>
    <line x1="{width - 26}" y1="16" x2="{width - 12}" y2="16"/>
    <line x1="{width - 16}" y1="12" x2="{width - 16}" y2="26"/>
    <line x1="12" y1="{height - 16}" x2="26" y2="{height - 16}"/>
    <line x1="16" y1="{height - 26}" x2="16" y2="{height - 12}"/>
    <line x1="{width - 26}" y1="{height - 16}" x2="{width - 12}" y2="{height - 16}"/>
    <line x1="{width - 16}" y1="{height - 26}" x2="{width - 16}" y2="{height - 12}"/>
  </g>

  <!-- Top Technical Header Bar -->
  <rect x="36" y="36" width="{width - 72}" height="34" fill="#0b3866" rx="2"/>
  <text x="50" y="58" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="12" font-weight="700" fill="#ffffff" letter-spacing="1">GROWTECH ENGINEERS • INDUSTRIAL SPECIFICATION ARCHIVE</text>
  <rect x="{width - 170}" y="43" width="120" height="20" fill="#198754" rx="2"/>
  <text x="{width - 110}" y="57" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#ffffff" text-anchor="middle">{category_code}</text>

  <!-- Main Illustration / Schematic Symbol -->
  <g transform="translate(0, 0)">
    {icon_content}
  </g>

  <!-- Center Focal Box -->
  <rect x="60" y="325" width="{width - 120}" height="105" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5" rx="4"/>
  <rect x="60" y="325" width="6" height="105" fill="#198754" rx="2"/>

  <!-- Title & Subtitle -->
  <text x="85" y="360" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="20" font-weight="800" fill="#0b3866">{title}</text>
  <text x="85" y="385" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="13" font-weight="500" fill="#475569">{subtitle}</text>
  <text x="85" y="412" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="#198754">MANESAR FACILITY • GROWTECH PRECISION STANDARDS</text>

  <!-- Technical Watermark / Compliance Notice -->
  <rect x="36" y="{height - 56}" width="{width - 72}" height="28" fill="#f1f5f9" stroke="#e2e8f0" stroke-width="1"/>
  <circle cx="52" cy="{height - 42}" r="4" fill="#0b3866"/>
  <text x="66" y="{height - 38}" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="#64748b" letter-spacing="0.5">NOTICE: TEMPORARY TECHNICAL PLACEHOLDER — ACTUAL UNIT PHOTO TO BE UPLOADED BY OWNER</text>
  <text x="{width - 50}" y="{height - 38}" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="10" font-weight="700" fill="#0b3866" text-anchor="end">GE-PLH-2024</text>
</svg>'''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(svg)

# Generate Products Placeholders
create_technical_placeholder(
    os.path.join(PRODUCTS_DIR, 'jigs_fixtures_placeholder.svg'),
    'Jigs &amp; Fixtures Assembly',
    'Custom Machining, Welding &amp; Assembly Clamping Fixtures for Automotive &amp; Sheet Metal',
    'CATEGORY: JIG-01',
    'jig'
)

create_technical_placeholder(
    os.path.join(PRODUCTS_DIR, 'receiving_gauges_placeholder.svg'),
    'Receiving &amp; Checking Gauges',
    'Dial Indicator Variable Stations &amp; Contour Flush/Gap Inspection Master Bases',
    'CATEGORY: GAUGE-02',
    'gauge'
)

create_technical_placeholder(
    os.path.join(PRODUCTS_DIR, 'press_tools_placeholder.svg'),
    'Tandem Press Tools &amp; Stamping Dies',
    'Hardened D2/D3 Piercing, Blanking, Forming &amp; Deep Draw Stamping Dies',
    'CATEGORY: PRESS-03',
    'press'
)

create_technical_placeholder(
    os.path.join(PRODUCTS_DIR, 'hydraulic_press_placeholder.svg'),
    'Industrial Hydraulic Presses',
    'Heavy-Duty Forming, Bushing Insertion &amp; Deep-Drawing Hydraulic Press Units',
    'CATEGORY: HYD-04',
    'press'
)

create_technical_placeholder(
    os.path.join(PRODUCTS_DIR, 'trolleys_racks_placeholder.svg'),
    'Material Handling Trolleys &amp; Racks',
    'Line-Side Parts Kitting Carts, FIFO Roller Racks &amp; Protective Component Nesting',
    'CATEGORY: LOGISTICS-05',
    'rack'
)

create_technical_placeholder(
    os.path.join(PRODUCTS_DIR, 'engineering_solutions_placeholder.svg'),
    'Plant Engineering &amp; Process Optimization',
    'Capacity Enhancement, Layout Planning, Kaizen &amp; Poka-Yoke Tooling Upgrades',
    'CATEGORY: ENG-06',
    'engineering'
)

# Factory & Infrastructure Placeholders
create_technical_placeholder(
    os.path.join(FACTORY_DIR, 'factory_infrastructure_placeholder.svg'),
    'Manesar Manufacturing Facility',
    'Main Market, Fazalwas, Tauru Road, Pachgaon, Manesar Industrial Corridor',
    'FACILITY: PLANT-01',
    'factory'
)

create_technical_placeholder(
    os.path.join(FACTORY_DIR, 'machinery_lathe_milling.svg'),
    'Machining &amp; Toolroom Equipment',
    'Precision Lathes, Heavy Milling Machines, Surface Grinders &amp; Radial Drills',
    'EQUIPMENT: TOOLROOM',
    'tool'
)

create_technical_placeholder(
    os.path.join(FACTORY_DIR, 'quality_inspection_lab.svg'),
    'Quality &amp; Inspection Station',
    'Precision Granite Surface Tables, Digital Height Gauges &amp; Calibrated Instruments',
    'QUALITY: QA-METROLOGY',
    'gauge'
)

create_technical_placeholder(
    os.path.join(FACTORY_DIR, 'assembly_bay.svg'),
    'Tooling Assembly &amp; Try-out Bay',
    'Tool Assembly Stations, Clamping Inspection &amp; Die Trial Setup Beds',
    'SHOPFLOOR: BAY-A',
    'jig'
)

# Milestone Placeholders for News & Events
create_technical_placeholder(
    os.path.join(FACTORY_DIR, 'milestone_inspection.svg'),
    'Quality Metrology Station Upgrade',
    'Enhancement of precision granite inspection tables and micrometric height gauges',
    'EVENT: QA-UPGRADE',
    'gauge'
)

create_technical_placeholder(
    os.path.join(FACTORY_DIR, 'milestone_tooling.svg'),
    'Tandem Tooling Set Dispatch',
    'Successful try-out and dispatch of multi-stage press tooling for automotive sub-assemblies',
    'EVENT: TOOL-DISPATCH',
    'press'
)

create_technical_placeholder(
    os.path.join(FACTORY_DIR, 'milestone_handling.svg'),
    'Material Handling Bay Expansion',
    'Dedicated fabrication area for customized line-side trolleys and FIFO storage racks',
    'EVENT: SHOP-EXPANSION',
    'rack'
)

create_technical_placeholder(
    os.path.join(FACTORY_DIR, 'milestone_foundation.svg'),
    'Establishment of Growtech Engineers',
    'Commencement of manufacturing operations under Mr. Naresh Kumar at Pachgaon, Manesar',
    'EVENT: INAUGURAL-2023',
    'factory'
)

# Customer Segment Badges (Representing manufacturing partner sectors without fake logos)
customer_segments = [
    ('cust_auto_tier1.svg', 'Automotive Tier-1 &amp; Tier-2', 'Chassis, Suspension &amp; Body Shell Suppliers'),
    ('cust_sheetmetal.svg', 'Sheet Metal Stamping Units', 'Press Work &amp; Formed Metal Enclosures'),
    ('cust_precision_eng.svg', 'Precision Machining Vendors', 'CNC Turn-Mill &amp; Component Fabricators'),
    ('cust_industrial_equip.svg', 'Industrial Equipment Makers', 'Machinery, Pumps &amp; Fluid Handling'),
    ('cust_assembly_tech.svg', 'Sub-Assembly &amp; Kitting Plants', 'Automated Production &amp; Material Logistics')
]

for filename, title, sub in customer_segments:
    cust_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 100" width="100%" height="100%">
  <rect width="280" height="100" fill="#ffffff" rx="4" stroke="#e2e8f0" stroke-width="1.5"/>
  <rect x="0" y="0" width="6" height="100" fill="#0b3866" rx="2"/>
  <g transform="translate(18, 16)">
    <circle cx="20" cy="20" r="16" fill="#f1f5f9" stroke="#0b3866" stroke-width="1.5"/>
    <text x="20" y="25" font-family="'Segoe UI', Roboto, sans-serif" font-size="14" font-weight="800" fill="#198754" text-anchor="middle">GE</text>
    <text x="46" y="16" font-family="'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="700" fill="#0b3866">{title}</text>
    <text x="46" y="34" font-family="'Segoe UI', Roboto, sans-serif" font-size="10.5" font-weight="500" fill="#64748b">{sub}</text>
    <line x1="46" y1="42" x2="245" y2="42" stroke="#e2e8f0" stroke-width="1"/>
    <text x="46" y="55" font-family="'Segoe UI', Roboto, sans-serif" font-size="9" font-weight="600" fill="#198754">VERIFIED MANUFACTURING SECTOR</text>
  </g>
</svg>'''
    with open(os.path.join(CUSTOMERS_DIR, filename), 'w', encoding='utf-8') as f:
        f.write(cust_svg)

print("All industrial assets and placeholders generated successfully.")
