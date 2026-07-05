$baseUrl = 'http://127.0.0.1:8080/api/v1'
$docs = @(
    @{ title='Urban Mobility Intelligence — APAC City Guide'; source='domain-urban-mobility'; content='Urban mobility in APAC cities faces unique challenges including extreme population density, mixed transport modes, and rapid urbanization.

TRAFFIC CONGESTION MANAGEMENT:
- Adaptive Traffic Signal Control (ATSC) reduces urban congestion by 20-30%. Singapore LTA deploys ATSC across 3,000+ intersections. Jakarta Electronic Road Pricing reduced CBD traffic 18%.
- Congestion index above 70/100 signals critical intervention needed. Deploy variable message signs, rerouting algorithms, and demand-responsive transit.
- Peak hour (07:00-09:00, 17:00-19:00) requires 40% more capacity than off-peak.

PUBLIC TRANSIT OPTIMIZATION:
- Transit mode share target: 75%+ for sustainable APAC cities. Singapore achieves 67%, Bangkok 43%.
- Bus rapid transit (BRT) implementation increases ridership 25-40% vs regular bus.
- MRT/LRT first/last mile connectivity gap causes 30% ridership loss. Solutions: park-and-ride, bike sharing, feeder buses within 500m of stations.
- Real-time passenger information systems increase satisfaction by 35%.

ROAD SAFETY:
- APAC road fatality rate: 17.4 per 100,000 population (WHO 2023). Target: below 10 by 2030.
- Speed cameras reduce fatalities 20-30%. Intersection safety cameras cut accidents 40%.
- Smart incident detection via CCTV and AI reduces response time from 12 min to 4 min.

EV AND SUSTAINABLE TRANSPORT:
- APAC EV adoption growing 45% year over year. Key barrier: charging infrastructure.
- Cycling infrastructure investment yields 5:1 economic return. Protected lanes increase cycling 80%.
- Micromobility (e-scooters, bikes) handles 15% of urban trips under 5km.

RECOMMENDED ACTIONS FOR HIGH CONGESTION:
1. Deploy adaptive signal control on identified bottleneck corridors immediately
2. Increase public transit frequency 25% during peak hours
3. Implement demand-based parking pricing in high-demand zones
4. Launch real-time multimodal journey planner app integration
5. Establish park-and-ride facilities at city periphery transit hubs
6. Create incentive program for work-from-home (reduces peak demand 15-20%)' },
    @{ title='Healthcare Access & Community Wellness — APAC Intelligence'; source='domain-healthcare'; content='Community healthcare intelligence for APAC cities and regions. Evidence-based insights for health authority decision-making.

HOSPITAL CAPACITY MANAGEMENT:
- Bed occupancy rate above 85% triggers surge capacity protocol. APAC average: 76% (WHO 2023).
- Optimal occupancy: 75-85% for efficient operations with buffer for emergencies.
- Emergency department wait time above 4 hours indicates overcrowding and ambulance diversion risk.
- Telemedicine diverts 25-35% of non-emergency ER visits. Post-COVID adoption increased 400%.
- Patient discharge optimization reduces length of stay by 1.2 days on average.

DISEASE SURVEILLANCE:
- Dengue: Wolbachia mosquito release reduces dengue by 77% (Singapore NEA data). Cluster detection threshold: 3+ cases in 200m radius triggers vector control.
- Respiratory illness: AQI correlation: every 10-point AQI increase raises respiratory admissions 3%.
- Syndromic surveillance: monitor pharmacy sales (paracetamol spikes signal outbreak 5-7 days ahead).

VACCINATION AND PREVENTIVE CARE:
- Coverage below 80% for key vaccines creates herd immunity gap.
- Mobile vaccination units increase coverage in underserved communities by 40%.
- School-based vaccination programs achieve 95%+ coverage vs 70% walk-in clinic rates.

MENTAL HEALTH:
- APAC mental health burden increasing 23% post-pandemic.
- Digital mental health platforms scale access 10x vs in-person.
- Workplace wellness programs reduce absenteeism 25% and presenteeism 10%.

RECOMMENDED ACTIONS:
1. Activate surge capacity if bed occupancy exceeds 85%
2. Deploy mobile health units to underserved communities (areas more than 5km from nearest clinic)
3. Implement ER triage AI to identify sepsis, stroke, MI within 2 minutes of arrival
4. Launch community health worker program (1 per 500 households reduces preventable admissions 20%)
5. Fast-track telemedicine for follow-up care (reduces unnecessary ER visits by 30%)' },
    @{ title='Environmental Sustainability & Climate Resilience — APAC Intelligence'; source='domain-environment'; content='Environmental intelligence for APAC community decision-making.

AIR QUALITY (AQI) MANAGEMENT:
- AQI Categories: Good (0-50), Moderate (51-100), Unhealthy Sensitive (101-150), Unhealthy (151-200).
- PM2.5 is primary health concern in APAC. Sources: vehicles (40%), industry (35%), open burning (15%).
- AQI above 100: issue advisory for sensitive groups (elderly, children, respiratory conditions).
- AQI above 150: close schools and outdoor events; activate N95 mask distribution.
- Low Emission Zones reduce city-center PM2.5 by 18-25%.
- Vehicle emission standards: Euro 6 compliance reduces NOx 80% and PM 90% vs older standards.

CARBON EMISSIONS:
- APAC cities account for 37% of global urban emissions. Net-zero target: 2050 (Paris Agreement).
- Building sector: 40% of city emissions. Green building certification reduces energy use 30-50%.
- Urban forests: 1 hectare absorbs 2.8 tonnes CO2/year and reduces urban heat 2-8 degrees Celsius.
- Carbon pricing at USD 50-100 per tonne CO2 effectively drives industry emission reduction.

WATER QUALITY:
- WHO safe drinking water standard: less than 1 E.coli CFU/100ml. Monthly testing required.
- Water loss (non-revenue water): APAC average 28%. Target below 15%. Smart meters reduce 20-30%.
- Flood risk: 1-in-100-year flood events becoming 1-in-20 due to climate change in APAC.
- Green infrastructure (rain gardens, permeable paving) reduces urban runoff 40-80%.

RECOMMENDED ACTIONS:
1. Deploy IoT air quality sensor network (1 sensor per 2km squared minimum for accurate mapping)
2. Implement green building retrofit incentives (30-50% subsidy for energy efficiency upgrades)
3. Establish urban carbon sequestration program (target 25% green cover in urban areas)
4. Launch water efficiency campaign and smart meter rollout (target NRW below 15%)
5. Integrate climate risk into urban planning (flood hazard maps, heat island mapping)' },
    @{ title='Citizen Services & Digital Government — APAC Intelligence'; source='domain-citizen-services'; content='Citizen services intelligence for improving government responsiveness and digital adoption in APAC.

SERVICE REQUEST MANAGEMENT:
- Average resolution time: APAC municipal services 5-10 days. Target: below 3 days for standard requests.
- Top request categories: road/infrastructure (35%), waste collection (20%), permits (18%), safety (12%).
- SLA breach: unresolved requests more than 7 days increase complaint volume 3x.
- AI-powered triage automates routing for 70% of requests, reducing manual handling costs 45%.
- Proactive status notifications via SMS and WhatsApp reduce follow-up calls by 60%.

DIGITAL TRANSFORMATION:
- APAC e-government adoption: Singapore 97%, South Korea 95%, Thailand 67%, Indonesia 52%.
- Digital service adoption increases citizen satisfaction score by 1.2 points on 5-point scale.
- Mobile-first design critical: 78% of APAC citizens access government services via mobile.
- Digital literacy barrier: 23% of adults in APAC cannot use digital services independently.

CITIZEN SATISFACTION DRIVERS:
- Key satisfaction drivers: speed of resolution (40%), communication quality (30%), ease of access (20%).
- Feedback loops: satisfaction surveys after every service interaction improves scores 25%.
- Participatory budgeting increases satisfaction 40%.

RECOMMENDED ACTIONS:
1. Implement AI-powered service request triage and auto-routing
2. Deploy omnichannel service portal (web, mobile app, WhatsApp, phone, in-person)
3. Establish 24/7 AI chatbot for Tier 1 queries (top 20 FAQs handle 60% of volume)
4. Create real-time SLA dashboard visible to citizens (transparency reduces complaints 35%)
5. Launch assisted digital program for seniors and low-income communities' },
    @{ title='Disaster Response & Community Resilience — APAC Intelligence'; source='domain-disaster-response'; content='Disaster risk reduction and emergency management intelligence for APAC. APAC bears 70% of global disaster losses (UN-ESCAP 2023).

EARLY WARNING SYSTEMS:
- Typhoon: 72-hour warning enables 85% evacuation compliance. 24-hour warning: 60%.
- Flood: river gauge and rainfall data provide 6-12 hour warning. Flash flood warning: 1-3 hours. Water level above 80% of flood stage triggers Evacuation Level 1.
- Earthquake: P-wave detection provides 10-60 second warning (J-Alert system Japan).
- Multi-hazard early warning: SMS + siren + app + radio reaches 90%+ population in 15 minutes.

RESOURCE PRE-POSITIONING:
- Pre-disaster resource positioning reduces response time from 48h to 12h.
- Strategic stockpile: 72-hour supplies for 30% of at-risk population.
- Community-based stockpiles: 50 households per cache, GPS-tagged, refreshed annually.
- Logistics pre-planning: identify primary and 2 backup routes for each evacuation zone.

COMMUNITY RESILIENCE:
- Community first responder training (1 per 50 households) reduces mortality 30% in first 72 hours.
- Vulnerable population mapping: elderly, disabled, pregnant women, children under 5 are priority evacuation.
- Simulation exercises: quarterly drills maintain 85% evacuation compliance.

RECOMMENDED ACTIONS:
1. Establish 24/7 Emergency Operations Centre with real-time multi-hazard monitoring
2. Pre-position resources in high-risk zones 48 hours before forecasted typhoon or flood
3. Activate community volunteer network immediately upon Level 1 alert declaration
4. Deploy rapid needs assessment teams within 2 hours of disaster onset
5. Coordinate with telecom operators for priority restoration of communication networks' },
    @{ title='Education & Lifelong Learning — APAC Intelligence'; source='domain-education'; content='Education intelligence for improving learning outcomes, access, and equity across APAC communities.

ENROLLMENT AND ATTENDANCE:
- APAC net enrollment ratio: primary 95%, secondary 79%, tertiary 43% (UNESCO 2023).
- Attendance below 80% strongly predicts dropout. Early intervention at 85% attendance threshold.
- Causes of absenteeism: economic (child labor, transport cost 45%), health (25%), safety (15%), disengagement (15%).
- Conditional cash transfer programs increase attendance 20-30% among vulnerable populations.
- School feeding programs increase attendance 15% and improve cognitive function 10%.

LEARNING OUTCOMES:
- PISA 2022: Singapore number 1 globally in Math and Science. APAC average below OECD in reading.
- Learning poverty (cannot read simple text by age 10): APAC average 53%.
- Foundational literacy and numeracy intervention by Grade 3 prevents 80% of learning poverty.
- Teacher quality accounts for 30% of variance in student outcomes.
- Class size below 25 improves outcomes 12% vs above 35 students.

TECHNOLOGY IN EDUCATION:
- EdTech adoption accelerated 300% post-COVID. Blended learning improves outcomes 15-25% vs pure classroom.
- Adaptive learning platforms identify knowledge gaps and personalize content, improving proficiency 30%.
- Digital divide: 23% of APAC students lack reliable internet for remote learning.

RECOMMENDED ACTIONS:
1. Deploy early warning system for students at risk of dropout (attendance and grade predictive model)
2. Implement structured pedagogical coaching for bottom-quartile performing teachers
3. Provide connectivity solutions for students in digital-poor areas
4. Launch STEM enrichment program in underperforming districts targeting girls and rural communities
5. Create alternative pathway programs for school leavers (apprenticeship, vocational bridge courses)' },
    @{ title='Energy & Smart Utilities — APAC Intelligence'; source='domain-energy-utilities'; content='Energy and utilities intelligence for smart city operations in APAC.

ELECTRICITY GRID MANAGEMENT:
- Grid load above 90%: critical risk of brownout. Activate demand response immediately.
- Peak demand management: time-of-use tariffs shift 15-20% of load to off-peak.
- Smart meters enable real-time demand monitoring and automated demand response.
- Grid frequency stability: maintain 49.8-50.2 Hz. Below 49.5 Hz triggers automatic load shedding.
- Virtual power plants aggregate distributed solar and battery to provide flexible capacity.

RENEWABLE ENERGY:
- APAC solar potential: 4-6 kWh per m2 per day. Rooftop solar payback period: 5-8 years.
- Offshore wind capacity growing 40% year over year in APAC.
- Battery storage: Lithium iron phosphate (LFP) most common. Cost down 90% since 2010.
- Renewable curtailment above 5% indicates grid needs storage or flexible demand response.
- Carbon intensity target: below 300g CO2 per kWh by 2030 (current APAC average: 550g CO2 per kWh).

WATER UTILITIES:
- Non-revenue water (NRW): APAC average 28%. Best practice: Singapore 5%, Tokyo 3%.
- Pressure management reduces pipe burst frequency 50% and physical NRW 20-30%.
- Smart water meters detect household leaks saving 15-20% water consumption.

RECOMMENDED ACTIONS:
1. Implement real-time grid monitoring with AI anomaly detection
2. Launch demand response program targeting top 100 commercial consumers
3. Accelerate rooftop solar permitting: target 5-day approval
4. Deploy pressure management zones across distribution network (target NRW below 15%)
5. Implement smart street lighting (sensor-based dimming saves 30-50% energy cost)
6. Create green building rating incentive: property tax rebate for certified green buildings' },
)

foreach ($doc in $docs) {
    $body = @{ title=$doc.title; content=$doc.content; source=$doc.source; tenant_id='default' } | ConvertTo-Json -Depth 3
    try {
        Invoke-RestMethod -Uri "$baseUrl/ingest/seed-dev" -Method POST -ContentType 'application/json' -Body $body | Out-Null
        Write-Host "✅ $($doc.title)"
    } catch { Write-Host "❌ $($doc.title): $($_.Exception.Message)" }
}
Write-Host "Done! $($docs.Count) documents seeded."
