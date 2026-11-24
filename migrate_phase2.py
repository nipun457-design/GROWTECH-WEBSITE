"""
Phase 2 Database Migration & Schema Setup for GROWTECH ENGINEERS
Preserves all existing enquiries and data.
Creates tables for users, products, product_images, company_content, gallery, certificates, and news_items.
Seeds initial data if tables are empty.
"""
import os
import json
import db

def migrate():
    conn = db.get_connection()
    # Initialize all tables for SQLite or PostgreSQL
    db.init_schema(conn)
    cursor = conn.cursor()

    # --- Seed Initial Products if table is empty ---
    cursor.execute("SELECT COUNT(*) as cnt FROM products")
    if cursor.fetchone()['cnt'] == 0:
        initial_products = [
            {
                'title': 'Jigs & Fixtures',
                'slug': 'jigs-fixtures',
                'category': 'Tooling & Clamping',
                'category_slug': 'jigs-fixtures',
                'tag': 'Precision Tooling',
                'summary': 'Custom welding jigs, CNC machining fixtures, height checking fixtures with automation, and cable taping fixtures.',
                'description': 'Growtech Engineers manufactures custom precision jigs and fixtures built to client component drawings and GD&T tolerances. Engineered for automotive sub-assemblies, tubular welding lines, and zero-defect production repeatability.',
                'features': json.dumps([
                    'Height checking fixtures with automation & digital feedback',
                    'Tap bending height checking fixtures',
                    'Taping fixtures for cable and wire harness assemblies',
                    'Hardened locating pins and wear-resistant guide bushes'
                ]),
                'applications': json.dumps(['Automotive sub-assemblies', 'BIW welding lines', 'Cable harness taping', 'Machining clamping setups']),
                'image': 'products/jigs_fixtures_real.jpg',
                'video_url': '',
                'is_featured': 1,
                'is_published': 1,
                'status_note': 'Actual delivered project photo: Height Checking Fixture with Automation'
            },
            {
                'title': 'Receiving Gauges',
                'slug': 'receiving-gauges',
                'category': 'Quality & Inspection',
                'category_slug': 'receiving-gauges',
                'tag': 'Inspection Gauges',
                'summary': 'Precision mechanical receiver gauges, housing assembly receiving gauges, and contour profile checking stations.',
                'description': 'Engineered to verify critical profile points, hole positions, surface contours, and flush-and-gap tolerances on shop floors. Growtech receiving gauges streamline quality verification for stampings and assemblies.',
                'features': json.dumps([
                    'Housing assembly receiving gauges with dial indicator stations',
                    'Precision ground master reference surfaces on hardened tool steel',
                    'Profile checking templates matching component 3D contours',
                    'Robust aluminum and steel composite base plates'
                ]),
                'applications': json.dumps(['Housing assemblies', 'Sheet metal stamped panels', 'Tubular chassis parts', 'Component QA inspection']),
                'image': 'products/receiving_gauge_real.jpg',
                'video_url': '',
                'is_featured': 1,
                'is_published': 1,
                'status_note': 'Actual delivered project photo: Housing Assembly Receiving Gauge'
            },
            {
                'title': 'Tandem Press Tools & Dies',
                'slug': 'press-tools',
                'category': 'Sheet Metal Tooling',
                'category_slug': 'press-tools',
                'tag': 'Stamping Dies',
                'summary': 'Tandem press tools, sheet bending dies, hole cutting dies, blanking dies, and forming tooling for sheet metal parts.',
                'description': 'Built for high stroke rates, extended tool life, and consistent metallurgical integrity. Engineered with high-grade tool steels (D2/D3) and precision-machined profiles for reliable metal forming.',
                'features': json.dumps([
                    'Dies for precision sheet bending and folding operations',
                    'Dies for hole cutting, piercing, and blanking',
                    'Modular punch and die inserts for ease of maintenance & regrinding',
                    'Standardized guide pillars, ball cages, and die springs'
                ]),
                'applications': json.dumps(['Automotive sheet metal brackets', 'Bended chassis reinforcements', 'Metal enclosures', 'Stamping production']),
                'image': 'products/press_tool_bending.jpg',
                'video_url': '',
                'is_featured': 1,
                'is_published': 1,
                'status_note': 'Actual delivered project photo: Die for Sheet Bending'
            },
            {
                'title': 'Hydraulic Presses',
                'slug': 'hydraulic-presses',
                'category': 'Machinery & Tooling',
                'category_slug': 'hydraulic-presses',
                'tag': 'Hydraulic Forming',
                'summary': 'Hydraulic presses and progressive tooling for hydraulic press forming, bushing insertion, and component drawing.',
                'description': 'Industrial-grade hydraulic press setups and progressive press tools engineered with rigid frame construction, reliable hydraulic circuits, and dual-hand safety controls.',
                'features': json.dumps([
                    'Progressive tools custom-built for hydraulic press operations',
                    'Rigid frame construction with low deflection under peak tonnage',
                    'Pressure limit and stroke adjustments for repeatable forming',
                    'Bushing pressing, bearing insertion, and blanking applications'
                ]),
                'applications': json.dumps(['Component drawing & forming', 'Bushing & bearing insertion', 'Metal pressing operations', 'Progressive stamping']),
                'image': 'products/hydraulic_press_tool.jpg',
                'video_url': '',
                'is_featured': 1,
                'is_published': 1,
                'status_note': 'Actual delivered project photo: Progressive Tools for Hydraulic Presses'
            },
            {
                'title': 'Trolleys & Racks',
                'slug': 'trolleys-racks',
                'category': 'Material Handling',
                'category_slug': 'trolleys-racks',
                'tag': 'Shop Floor Logistics',
                'summary': 'Heavy-duty industrial material handling trolleys, line-side parts kitting carts, and FIFO storage racks.',
                'description': 'Designed to protect finished and in-process parts from transit damage while streamlining shop floor material logistics. Fabricated with tubular steel and polyurethane component separators.',
                'features': json.dumps([
                    'Custom nesting contours lined with protective PU/rubber to prevent part scratching',
                    'Heavy-gauge tubular steel fabrication with durable industrial finish',
                    'High-load industrial casters with directional locks and wheel brakes',
                    'Modular line-side feed carts for efficient lean production flow'
                ]),
                'applications': json.dumps(['Assembly line-side kitting', 'In-transit press part handling', 'Warehouse inventory management', 'Machine-to-machine transfer']),
                'image': 'products/trolleys_racks_placeholder.svg',
                'video_url': '',
                'is_featured': 0,
                'is_published': 1,
                'status_note': 'Temporary technical placeholder — actual workshop trolley photo to be uploaded by owner'
            },
            {
                'title': 'Engineering Solutions & Consultancy',
                'slug': 'engineering-solutions',
                'category': 'Industrial Solutions',
                'category_slug': 'engineering-solutions',
                'tag': 'Process Optimization',
                'summary': 'Cooling panels for die casting machines, tapping machines, plant engineering, layout planning, and Kaizen / Poka-Yoke.',
                'description': 'Leveraging 22+ years of hands-on engineering experience, Growtech Engineers provides specialized shop floor machinery, cooling panels, plant layout planning, and Kaizen/Poka-Yoke mistake-proofing solutions.',
                'features': json.dumps([
                    'Cooling panels for die casting machines',
                    'Dedicated tapping machines and low-cost automation aids',
                    'Plant engineering, layout planning & capacity enhancement',
                    'Cost reduction projects through Kaizen and Poka-Yoke mechanisms'
                ]),
                'applications': json.dumps(['Die casting facilities', 'Tapping operations', 'Shop floor layout reorganization', 'Production de-bottlenecking']),
                'image': 'products/cooling_panel_real.jpg',
                'video_url': '',
                'is_featured': 0,
                'is_published': 1,
                'status_note': 'Actual delivered project photo: Cooling Panel for Die Casting Machine'
            }
        ]

        for p in initial_products:
            cursor.execute('''
                INSERT INTO products (title, slug, category, category_slug, tag, summary, description, features, applications, image, video_url, is_featured, is_published, status_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (p['title'], p['slug'], p['category'], p['category_slug'], p['tag'], p['summary'], p['description'], p['features'], p['applications'], p['image'], p['video_url'], p['is_featured'], p['is_published'], p['status_note']))
            pid = cursor.lastrowid
            # Also add to product_images
            cursor.execute('''
                INSERT INTO product_images (product_id, image_path, caption, is_primary)
                VALUES (?, ?, ?, 1)
            ''', (pid, p['image'], p['title']))

        conn.commit()
        print(f"Seeded {len(initial_products)} products.")

    # --- Seed Initial News if table is empty ---
    cursor.execute("SELECT COUNT(*) as cnt FROM news_items")
    if cursor.fetchone()['cnt'] == 0:
        initial_news = [
            {
                'title': 'Official Udyam Registration (UDYAM-HR-05-0093212)',
                'category': 'Government Registration',
                'summary': 'Growtech Engineers officially registered under the Ministry of Micro, Small & Medium Enterprises, Government of India, classified under NIC Code 28221 (Manufacture of machine tools for turning, drilling, milling, shaping, grinding).',
                'content': 'Official Government of India certification received on 31/01/2024 confirming classification as Micro Manufacturing Enterprise under Udyam registration number UDYAM-HR-05-0093212.',
                'date_display': 'January 31, 2024',
                'image': 'certificates/udyam_badge.svg',
                'is_real': 1,
                'is_published': 1
            },
            {
                'title': 'Commencement of Growtech Engineers Plant in Manesar',
                'category': 'Company Foundation',
                'summary': 'Manufacturing plant established at Main Market, Fazalwas, Tauru Road, Pachgaon, Manesar (Gurugram, Haryana) under the proprietorship of Mr. Naresh Kumar, bringing over 22 years of tooling and engineering experience.',
                'content': 'Commencement of full-scale manufacturing operations for jigs, fixtures, receiving gauges, and tandem press tools.',
                'date_display': 'September 2023',
                'image': 'factory/main_entrance.jpg',
                'is_real': 1,
                'is_published': 1
            },
            {
                'title': 'Commissioning of VMC VL1200 & MNTR Toolroom Setup',
                'category': 'Shop Floor Infrastructure',
                'summary': 'Installation and commissioning of VMC Machine (1200*650mm) and MNTR with DRO milling machines to support precision toolroom manufacturing, die making, and fixture assembly.',
                'content': 'Commissioned STM VL1200 vertical machining center and Hercules turret milling setups.',
                'date_display': 'October 2023',
                'image': 'factory/vmc_machine.jpg',
                'is_real': 1,
                'is_published': 1
            },
            {
                'title': 'Upcoming Plant Expansion & Technical Milestone',
                'category': 'Reserved Gallery Slot',
                'summary': 'Reserved space for upcoming company milestones, new machinery additions, or trade exhibition participations to be updated by the owner.',
                'content': 'Reserved gallery item.',
                'date_display': 'Upcoming',
                'image': 'factory/milestone_placeholder.svg',
                'is_real': 0,
                'is_published': 1
            }
        ]
        for n in initial_news:
            cursor.execute('''
                INSERT INTO news_items (title, category, summary, content, date_display, image, is_real, is_published)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (n['title'], n['category'], n['summary'], n['content'], n['date_display'], n['image'], n['is_real'], n['is_published']))
        conn.commit()
        print(f"Seeded {len(initial_news)} news items.")

    # --- Seed Initial Gallery if table is empty ---
    cursor.execute("SELECT COUNT(*) as cnt FROM gallery")
    if cursor.fetchone()['cnt'] == 0:
        initial_gallery = [
            {'title': 'Main Plant Entrance & Board', 'category': 'Factory', 'file_type': 'image', 'file_path': 'factory/main_entrance.jpg', 'caption': 'Main entrance on Tauru Road, Pachgaon, Manesar with official signboard'},
            {'title': 'Inner Shop Floor Infrastructure', 'category': 'Factory', 'file_type': 'image', 'file_path': 'factory/inner_infrastructure.jpg', 'caption': 'Internal shop floor layout with assembly benches and workstations'},
            {'title': 'Engineering & Office Administration', 'category': 'Factory', 'file_type': 'image', 'file_path': 'factory/office_room.jpg', 'caption': 'Planning and CAD review workstations'},
            {'title': 'Quality Metrology Room', 'category': 'Factory', 'file_type': 'image', 'file_path': 'factory/inspection_room.jpg', 'caption': 'Luthra granite surface plate and digital height gauge inspection'},
            {'title': 'STM VL1200 VMC Machine (1200*650mm)', 'category': 'Machinery', 'file_type': 'image', 'file_path': 'factory/vmc_machine.jpg', 'caption': 'Vertical machining center for die pocketing and fixture plates'},
            {'title': 'Hercules MNTR Milling with DRO', 'category': 'Machinery', 'file_type': 'image', 'file_path': 'factory/milling_machines.jpg', 'caption': 'Vertical turret milling machines equipped with digital readout'},
            {'title': 'Precision Centre Lathes in Operation', 'category': 'Machinery', 'file_type': 'image', 'file_path': 'factory/lathe_machines.jpg', 'caption': '4.5 ft & 6 ft lathe turning operations'},
            {'title': 'Sai Prime Precision Surface Grinders', 'category': 'Machinery', 'file_type': 'image', 'file_path': 'factory/surface_grinder.jpg', 'caption': 'Surface grinding stations for datum alignment'},
            {'title': 'Industrial Welding Stations', 'category': 'Machinery', 'file_type': 'image', 'file_path': 'factory/welding_machine.jpg', 'caption': 'Arc and portable welding equipment for fabrication'},
            {'title': 'Industrial Band Saw Machine', 'category': 'Machinery', 'file_type': 'image', 'file_path': 'factory/bandsaw_machine.jpg', 'caption': 'Raw material cutting and sizing setup'},
            {'title': 'Height Checking Fixture with Automation', 'category': 'Project', 'file_type': 'image', 'file_path': 'products/jigs_fixtures_real.jpg', 'caption': 'Completed automated inspection fixture for automotive client'},
            {'title': 'Housing Assembly Receiving Gauge', 'category': 'Project', 'file_type': 'image', 'file_path': 'products/receiving_gauge_real.jpg', 'caption': 'Multi-datum checking gauge for housing component'},
            {'title': 'Die for Sheet Bending', 'category': 'Project', 'file_type': 'image', 'file_path': 'products/press_tool_bending.jpg', 'caption': 'Hardened D2 tool steel sheet bending die set'},
            {'title': 'Progressive Tools for Hydraulic Press', 'category': 'Project', 'file_type': 'image', 'file_path': 'products/hydraulic_press_tool.jpg', 'caption': 'Progressive tooling assembly for forming operations'},
            {'title': 'Cooling Panel for Die Casting Machine', 'category': 'Project', 'file_type': 'image', 'file_path': 'products/cooling_panel_real.jpg', 'caption': 'Custom manufactured cooling panel engineering solution'}
        ]
        for g in initial_gallery:
            cursor.execute('''
                INSERT INTO gallery (title, category, file_type, file_path, caption, is_published)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (g['title'], g['category'], g['file_type'], g['file_path'], g['caption']))
        conn.commit()
        print(f"Seeded {len(initial_gallery)} gallery items.")

    # --- Seed Initial Certificates if table is empty ---
    cursor.execute("SELECT COUNT(*) as cnt FROM certificates")
    if cursor.fetchone()['cnt'] == 0:
        initial_certs = [
            {
                'title': 'Udyam Registration Certificate',
                'cert_number': 'UDYAM-HR-05-0093212',
                'issuing_authority': 'Ministry of Micro, Small & Medium Enterprises, Government of India',
                'issue_date': '31/01/2024',
                'file_path': 'certificates/udyam_badge.svg',
                'description': 'Official government recognition as Micro Manufacturing Enterprise under NIC 28221 (Manufacture of machine tools for turning, drilling, milling, shaping, grinding).',
                'is_published': 1
            },
            {
                'title': 'Goods & Services Tax Registration (GSTIN)',
                'cert_number': '06BIYPK7127F1ZV',
                'issuing_authority': 'Government of Haryana & Central Board of Indirect Taxes and Customs',
                'issue_date': 'July 2023',
                'file_path': 'factory/main_entrance.jpg',
                'description': 'Taxation registration certificate for manufacturing and engineering services.',
                'is_published': 1
            }
        ]
        for c in initial_certs:
            cursor.execute('''
                INSERT INTO certificates (title, cert_number, issuing_authority, issue_date, file_path, description, is_published)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (c['title'], c['cert_number'], c['issuing_authority'], c['issue_date'], c['file_path'], c['description'], c['is_published']))
        conn.commit()
        print(f"Seeded {len(initial_certs)} certificates.")

    # --- Seed Company Content Key-Values if empty ---
    cursor.execute("SELECT COUNT(*) as cnt FROM company_content")
    if cursor.fetchone()['cnt'] == 0:
        initial_content = {
            'company_name': 'GROWTECH ENGINEERS',
            'slogan': "GTE – Let's Get Growing",
            'tagline': 'Precision Tooling, Jigs & Fixtures, and Industrial Engineering Solutions',
            'business': 'Manufacturing machine components, parts, tooling, and industrial engineering solutions',
            'proprietor': 'Mr. Naresh Kumar',
            'proprietor_experience': '22+ Years of Engineering & Toolroom Experience',
            'established': 'September 2023',
            'gstin': '06BIYPK7127F1ZV',
            'udyam_number': 'UDYAM-HR-05-0093212',
            'udyam_type': 'Micro Enterprise (Manufacturing)',
            'nic_code': '28221 (Metal-forming machinery & machine tools)',
            'email': 'growtechengineers911@gmail.com',
            'phone_primary': '+91-9991535590',
            'phone_secondary': '+91-8930294103',
            'location': 'Main Market, Fazalwas, Tauru Road, Pachgaon, Manesar, Gurugram, Haryana – 122413, India',
            'city': 'Manesar, Gurugram',
            'state': 'Haryana',
            'pincode': '122413',
            'working_hours': 'Monday – Saturday: 08:30 AM – 07:30 PM (Sunday Closed)',
            'facilities_area': 'Total Area: 3,800 Sq. Ft. | Built-up Area: 2,650 Sq. Ft.',
            'manpower': '8 Technical Team Members (Fabrication, Automation & Tool/Fixture Mfg.)',
            'power_backup': '35 KVA Generator Facility Available',
            'vision': "TO PROVIDE THE ENGINEERING SOLUTIONS TO MAKE EVERYONE'S LIFE EASY & TO WIN THE CONFIDENCE OF STAKEHOLDERS.",
            'mission': "TO MAKE OUR ORGANIZATION BEST IN THE MARKET TO PROVIDE INDUSTRIAL SOLUTIONS WITH EFFECTIVE COST.",
            'intro_text': "Established in September 2023 by Mr. Naresh Kumar (bringing over 22 years of hands-on tooling experience), GROWTECH ENGINEERS (GTE) has positioned itself as a dependable tooling, machining, and engineering partner for component manufacturers in the Gurgaon–Manesar industrial belt."
        }
        for k, v in initial_content.items():
            cursor.execute('''
                INSERT INTO company_content (key_name, value)
                VALUES (?, ?)
            ''', (k, v))
        conn.commit()
        print(f"Seeded {len(initial_content)} company content keys.")

    conn.close()
    print("Database migration completed successfully.")

if __name__ == '__main__':
    migrate()
