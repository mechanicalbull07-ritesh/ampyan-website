# failure_database.py

from ai_engine.language_engine import normalize_failure_database_entries

FAILURE_DATABASE = [

# ================= ENGINE =================

# ================= ENGINE =================

{
"id":1,
"problem":"Spark Plug Worn",
"system":"engine",
"component":"spark plug",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"engine misfire",
"engine vibration",
"poor fuel economy",
"difficulty starting"
],

"questions":[
{"id":"q1","text":"Engine start karne me dikkat aa rahi hai?"},
{"id":"q2","text":"Acceleration pe jerk ya misfire feel hota hai?"}
],

"user_checks":[
"check if engine struggles to start"
],

"repair_cost":{"min":1000,"max":4000}
},

{
"id":2,
"problem":"Ignition Coil Failure",
"system":"engine",
"component":"ignition coil",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine misfire",
"loss of power",
"check engine light"
],

"questions":[
{"id":"q1","text":"Acceleration pe power loss feel hota hai?"},
{"id":"q2","text":"Check engine light ON hai?"}
],

"user_checks":[
"check if engine shakes during acceleration"
],

"repair_cost":{"min":2000,"max":8000}
},

{
"id":3,
"problem":"Fuel Injector Clogged",
"system":"fuel",
"component":"fuel injector",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine misfire",
"loss of power",
"poor fuel economy"
],

"questions":[
{"id":"q1","text":"Acceleration pe engine jerk karta hai?"},
{"id":"q2","text":"Mileage suddenly kam ho gaya hai?"}
],

"user_checks":[
"check if engine misfires during acceleration"
],

"repair_cost":{"min":2500,"max":7000}
},

{
"id":4,
"problem":"Clogged Air Filter",
"system":"engine",
"component":"air intake",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"poor acceleration",
"loss of power",
"reduced mileage"
],

"questions":[
{"id":"q1","text":"Car me pickup kam ho gaya hai?"},
{"id":"q2","text":"Mileage drop feel ho raha hai?"}
],

"user_checks":[
"inspect air filter condition"
],

"repair_cost":{"min":300,"max":1500}
},

{
"id":5,
"problem":"Dirty Throttle Body",
"system":"engine",
"component":"throttle body",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"rough idle",
"engine hesitation",
"engine stalls"
],

"questions":[
{"id":"q1","text":"Idle pe RPM up-down ho raha hai?"},
{"id":"q2","text":"Car kabhi-kabhi band ho jaati hai?"}
],

"user_checks":[
"observe unstable idle RPM"
],

"repair_cost":{"min":1500,"max":4000}
},

{
"id":6,
"problem":"Engine Mount Worn",
"system":"engine",
"component":"engine mount",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"engine vibration",
"thud sound during acceleration"
],

"questions":[
{"id":"q1","text":"Acceleration pe thud sound aati hai?"},
{"id":"q2","text":"Idle pe engine vibration zyada feel hota hai?"}
],

"user_checks":[
"observe engine movement while revving"
],

"repair_cost":{"min":3000,"max":10000}
},

{
"id":7,
"problem":"Timing Chain Wear",
"system":"engine",
"component":"timing chain",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"rattling noise from engine",
"engine noise at startup"
],

"questions":[
{"id":"q1","text":"Cold start pe rattling noise aati hai?"},
{"id":"q2","text":"Engine start karte hi ajeeb awaaz aati hai?"}
],

"user_checks":[
"listen for rattling sound during cold start"
],

"repair_cost":{"min":8000,"max":25000}
},

{
"id":8,
"problem":"Engine Vacuum Leak",
"system":"engine",
"component":"vacuum system",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"rough idle",
"high idle RPM"
],

"questions":[
{"id":"q1","text":"Idle pe RPM normal se zyada hai?"},
{"id":"q2","text":"Engine se hissing sound aati hai?"}
],

"user_checks":[
"listen for hissing sound"
],

"repair_cost":{"min":1500,"max":8000}
},

{
"id":9,
"problem":"MAF Sensor Fault",
"system":"engine",
"component":"maf sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine hesitation",
"poor acceleration"
],

"questions":[
{"id":"q1","text":"Acceleration me delay feel hota hai?"},
{"id":"q2","text":"Pickup smooth nahi lagta?"}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":3000,"max":9000}
},

{
"id":10,
"problem":"Oxygen Sensor Fault",
"system":"engine",
"component":"oxygen sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"check engine light",
"poor fuel economy"
],

"questions":[
{"id":"q1","text":"Check engine light ON hai?"},
{"id":"q2","text":"Fuel consumption badh gaya hai?"}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":3000,"max":9000}
},

{
"id":11,
"problem":"Low Coolant Level",
"system":"cooling",
"component":"coolant system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"engine overheating",
"overheating",
"engine temperature high",
"coolant warning light"
],

"questions":[
{
"id":"q1",
"text":"Coolant level low hai?",
"impact":{"yes":1.4,"no":0.6}
},
{
"id":"q2",
"text":"Temperature warning aa rahi hai?",
"impact":{"yes":1.5,"no":0.5}
}
],

"user_checks":[
"check coolant reservoir level"
],

"repair_cost":{"min":500,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":12,
"problem":"Radiator Fan Failure",
"system":"cooling",
"component":"radiator fan",
"severity":"high",
"urgency":"repair_immediately",
"probability":7,

"symptoms":[
"engine overheating",
"temperature high",
"fan not running"
],

"questions":[
{
"id":"q1",
"text":"Fan chal nahi raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Car traffic me overheat hoti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check if radiator fan turns on when engine is hot"
],

"repair_cost":{"min":2500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":13,
"problem":"Radiator Blocked",
"system":"cooling",
"component":"radiator",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"engine overheating",
"coolant temperature high"
],

"questions":[
{
"id":"q1",
"text":"Radiator fins blocked ya dirty lag rahe hain?",
"impact":{"yes":1.3,"no":0.7}
},
{
"id":"q2",
"text":"High speed pe bhi overheating ho rahi hai?",
"impact":{"yes":1.4,"no":0.6}
}
],

"user_checks":[
"inspect radiator fins"
],

"repair_cost":{"min":3000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":14,
"problem":"Thermostat Stuck Closed",
"system":"cooling",
"component":"thermostat",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine overheating quickly"
],

"questions":[
{
"id":"q1",
"text":"Engine jaldi heat ho jata hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Temperature suddenly shoot karta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe temperature rise"
],

"repair_cost":{"min":2000,"max":6000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":15,
"problem":"Water Pump Failure",
"system":"cooling",
"component":"water pump",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"coolant leak",
"engine overheating"
],

"questions":[
{
"id":"q1",
"text":"Coolant leak visible hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine continuously overheat ho raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check coolant leak near pump"
],

"repair_cost":{"min":4000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":16,
"problem":"Brake Pad Wear",
"system":"brake",
"component":"brake pads",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"squeaking while braking",
"reduced braking power"
],

"questions":[
{
"id":"q1",
"text":"Brake lagate time squeaking sound aati hai?",
"impact":{"yes":1.4,"no":0.6}
},
{
"id":"q2",
"text":"Brake performance weak feel ho raha hai?",
"impact":{"yes":1.5,"no":0.5}
}
],

"user_checks":[
"listen for brake noise"
],

"repair_cost":{"min":2500,"max":7000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":17,
"problem":"Brake Disc Warped",
"system":"brake",
"component":"brake disc",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"vibration while braking"
],

"questions":[
{
"id":"q1",
"text":"Brake lagate waqt steering vibrate karti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"High speed braking pe vibration zyada hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check steering vibration"
],

"repair_cost":{"min":4000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":18,
"problem":"Brake Fluid Low",
"system":"brake",
"component":"brake fluid",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"soft brake pedal",
"brake warning light"
],

"questions":[
{
"id":"q1",
"text":"Brake pedal soft lag raha hai?",
"impact":{"yes":1.5,"no":0.5}
},
{
"id":"q2",
"text":"Brake warning light ON hai?",
"impact":{"yes":1.4,"no":0.6}
}
],

"user_checks":[
"check brake fluid level"
],

"repair_cost":{"min":500,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":19,
"problem":"Brake Caliper Stuck",
"system":"brake",
"component":"brake caliper",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"car pulling to one side while braking"
],

"questions":[
{
"id":"q1",
"text":"Brake lagate waqt car ek side khich rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Ek wheel zyada heat ho raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check wheel heat after driving"
],

"repair_cost":{"min":3000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":20,
"problem":"ABS Sensor Fault",
"system":"brake",
"component":"abs sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"ABS warning light"
],

"questions":[
{
"id":"q1",
"text":"ABS light dashboard pe ON hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Brake lagate waqt ABS kaam nahi kar raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan ABS codes"
],

"repair_cost":{"min":2500,"max":9000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":21,
"problem":"Wheel Bearing Failure",
"system":"suspension",
"component":"wheel bearing",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"humming noise while driving"
],

"questions":[
{
"id":"q1",
"text":"Driving ke time humming ya ghurrr sound aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Speed badhne pe noise increase hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"listen for wheel noise"
],

"repair_cost":{"min":3000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":22,
"problem":"Shock Absorber Worn",
"system":"suspension",
"component":"shock absorber",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"car bouncing after bumps"
],

"questions":[
{
"id":"q1",
"text":"Speed breaker ke baad car bounce karti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Ride comfort kam ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"perform bounce test"
],

"repair_cost":{"min":4000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":23,
"problem":"Suspension Bush Wear",
"system":"suspension",
"component":"suspension bush",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"clunk noise on bumps"
],

"questions":[
{
"id":"q1",
"text":"Road bumps pe clunk sound aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Low speed pe bhi suspension noise aati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect bushings"
],

"repair_cost":{"min":1500,"max":6000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":24,
"problem":"Wheel Alignment Incorrect",
"system":"steering",
"component":"wheel alignment",
"severity":"low",
"urgency":"service_soon",
"probability":7,

"symptoms":[
"car pulling to one side",
"steering off center",
"uneven tire wear"
],

"questions":[
{
"id":"q1",
"text":"Car seedhi road pe ek side khich rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Steering center me nahi rehta?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe straight road behavior"
],

"repair_cost":{"min":800,"max":2500},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":25,
"problem":"Tire Pressure Low",
"system":"suspension",
"component":"tire",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"vehicle pulling",
"tire pressure warning"
],

"questions":[
{
"id":"q1",
"text":"Tire pressure warning light ON hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Car ek side pull kar rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check tire pressure"
],

"repair_cost":{"min":0,"max":500},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":26,
"problem":"Battery Weak",
"system":"electrical",
"component":"battery",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"slow engine cranking",
"dim headlights",
"battery warning light"
],

"questions":[
{
"id":"q1",
"text":"Car start slow ho rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Headlights dim lag rahe hain?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check battery voltage"
],

"repair_cost":{"min":3000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":27,
"problem":"Alternator Failure",
"system":"electrical",
"component":"alternator",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"battery warning light",
"battery draining quickly",
"electrical systems malfunction"
],

"questions":[
{
"id":"q1",
"text":"Battery bar-bar discharge ho rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Driving ke time battery light ON ho jaati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check battery voltage while engine running"
],

"repair_cost":{"min":5000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":28,
"problem":"Starter Motor Failure",
"system":"electrical",
"component":"starter motor",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine not cranking",
"clicking sound when starting"
],

"questions":[
{
"id":"q1",
"text":"Start karte time clicking sound aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine crank nahi ho raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"listen for clicking sound during ignition"
],

"repair_cost":{"min":4000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":29,
"problem":"Loose Battery Terminal",
"system":"electrical",
"component":"battery terminal",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"car not starting",
"dashboard flickering"
],

"questions":[
{
"id":"q1",
"text":"Dashboard lights flicker ho rahi hain?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Battery terminal loose lag raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect battery terminals"
],

"repair_cost":{"min":200,"max":800},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":30,
"problem":"Fuse Blown",
"system":"electrical",
"component":"fuse",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"electrical component not working",
"power loss in system"
],

"questions":[
{
"id":"q1",
"text":"Koi specific electrical feature kaam nahi kar raha?",
"impact":{"yes":1.4,"no":0.7}
},
{
"id":"q2",
"text":"Suddenly power loss hua hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"inspect fuse box"
],

"repair_cost":{"min":100,"max":500},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":31,
"problem":"Clutch Plate Worn",
"system":"transmission",
"component":"clutch plate",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"engine revs high but speed not increasing",
"burning smell from clutch",
"gear not shifting properly",
"hard gear shift"
],

"questions":[
{
"id":"q1",
"text":"RPM badh raha hai lekin speed nahi badh rahi?",
"impact":{"yes":1.5,"no":0.5}
},
{
"id":"q2",
"text":"Clutch se burning smell aati hai?",
"impact":{"yes":1.4,"no":0.6}
}
],

"user_checks":[
"observe RPM increase without speed increase"
],

"repair_cost":{"min":6000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":32,
"problem":"Clutch Cable Loose",
"system":"transmission",
"component":"clutch cable",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"clutch pedal feels loose",
"gear shifting difficult"
],

"questions":[
{
"id":"q1",
"text":"Clutch pedal loose feel ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Gear shift karna mushkil ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check clutch pedal free play"
],

"repair_cost":{"min":800,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":33,
"problem":"Gearbox Oil Low",
"system":"transmission",
"component":"gearbox",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"gear hard to shift",
"gearbox noise",
"gear not shifting properly",
"hard gear shift"
],

"questions":[
{
"id":"q1",
"text":"Gear shift hard ho gaya hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Gearbox se noise aa rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check gearbox oil level"
],

"repair_cost":{"min":800,"max":4000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":34,
"problem":"Gear Synchronizer Wear",
"system":"transmission",
"component":"gear synchronizer",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"gear hard to shift",
"gearbox noise",
"gear not shifting properly",
"hard gear shift"
],

"questions":[
{
"id":"q1",
"text":"Gear change karte waqt grinding feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Specific gear me issue zyada hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check if grinding occurs while shifting"
],

"repair_cost":{"min":10000,"max":35000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":35,
"problem":"Transmission Fluid Low",
"system":"transmission",
"component":"transmission fluid",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"gear slipping",
"delayed gear shifts"
],

"questions":[
{
"id":"q1",
"text":"Gear slip ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Gear shift delay ho raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check transmission fluid level"
],

"repair_cost":{"min":1000,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":36,
"problem":"AC Gas Low",
"system":"ac",
"component":"ac refrigerant",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"ac not cooling properly",
"weak airflow from vents"
],

"questions":[
{
"id":"q1",
"text":"AC cooling weak ho gayi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"AC chal raha hai par thandi hawa nahi aa rahi?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check AC cooling performance"
],

"repair_cost":{"min":1500,"max":4000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":37,
"problem":"AC Compressor Failure",
"system":"ac",
"component":"ac compressor",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"ac not cooling",
"loud noise from compressor"
],

"questions":[
{
"id":"q1",
"text":"AC bilkul cooling nahi kar raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"AC on karte hi noise aati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check compressor engagement"
],

"repair_cost":{"min":8000,"max":25000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":38,
"problem":"Cabin Air Filter Clogged",
"system":"ac",
"component":"cabin air filter",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"weak airflow",
"bad smell in cabin"
],

"questions":[
{
"id":"q1",
"text":"AC airflow weak lag raha hai?",
"impact":{"yes":1.4,"no":0.7}
},
{
"id":"q2",
"text":"Cabin me bad smell aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"inspect cabin air filter"
],

"repair_cost":{"min":300,"max":1500},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":39,
"problem":"AC Condenser Blocked",
"system":"ac",
"component":"ac condenser",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"ac cooling weak",
"ac cooling drops in traffic"
],

"questions":[
{
"id":"q1",
"text":"Traffic me AC cooling kam ho jati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Highway pe AC thik kaam karta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect condenser fins"
],

"repair_cost":{"min":2000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":40,
"problem":"Blower Motor Failure",
"system":"ac",
"component":"blower motor",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"no air from vents",
"blower not working"
],

"questions":[
{
"id":"q1",
"text":"AC vents se hawa nahi aa rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Blower bilkul kaam nahi kar raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"test blower fan speed"
],

"repair_cost":{"min":2000,"max":6000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":41,
"problem":"Fuel Pump Weak",
"system":"fuel",
"component":"fuel pump",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine hard to start",
"loss of power"
],

"questions":[
{
"id":"q1",
"text":"Car start karne me dikkat aa rahi hai?",
"impact":{"yes":1.4,"no":0.7}
},
{
"id":"q2",
"text":"Acceleration pe power loss feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"listen for fuel pump sound"
],

"repair_cost":{"min":4000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":42,
"problem":"Fuel Filter Clogged",
"system":"fuel",
"component":"fuel filter",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"engine hesitation",
"loss of power"
],

"questions":[
{
"id":"q1",
"text":"Acceleration me jerk feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Mileage kam ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check fuel filter replacement history"
],

"repair_cost":{"min":800,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":43,
"problem":"Fuel Pressure Regulator Fault",
"system":"fuel",
"component":"fuel pressure regulator",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"engine hesitation",
"poor fuel economy"
],

"questions":[
{
"id":"q1",
"text":"Fuel consumption badh gaya hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine smooth nahi chal raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe fuel pressure behavior"
],

"repair_cost":{"min":3000,"max":9000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":44,
"problem":"EVAP Purge Valve Fault",
"system":"fuel",
"component":"evap purge valve",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"check engine light",
"rough idle"
],

"questions":[
{
"id":"q1",
"text":"Check engine light ON hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Idle pe engine rough chal raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":2500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":45,
"problem":"Fuel Tank Vent Blocked",
"system":"fuel",
"component":"fuel tank vent",
"severity":"low",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"difficulty refueling",
"fuel smell near vehicle"
],

"questions":[
{
"id":"q1",
"text":"Fuel bharte time problem hoti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Car ke paas fuel smell aati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe fuel filling behavior"
],

"repair_cost":{"min":1500,"max":6000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":46,
"problem":"Horn Not Working",
"system":"electrical",
"component":"horn system",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"horn not producing sound"
],

"questions":[
{
"id":"q1",
"text":"Horn dabane pe awaaz nahi aa rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Horn kabhi-kabhi kaam karta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check horn fuse"
],

"repair_cost":{"min":500,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":47,
"problem":"Wiper Motor Failure",
"system":"electrical",
"component":"wiper motor",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"wipers not moving"
],

"questions":[
{
"id":"q1",
"text":"Wipers bilkul move nahi kar rahe?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Wiper switch kaam kar raha hai?",
"impact":{"yes":1.3,"no":0.7}
}
],

"user_checks":[
"test wiper operation"
],

"repair_cost":{"min":2000,"max":7000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":48,
"problem":"Headlight Bulb Burned",
"system":"electrical",
"component":"headlight bulb",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"headlight not working"
],

"questions":[
{
"id":"q1",
"text":"Headlight ON karne pe light nahi aa rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Ek side ki light band hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect headlight bulb"
],

"repair_cost":{"min":300,"max":2000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":49,
"problem":"Brake Light Switch Fault",
"system":"electrical",
"component":"brake light switch",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"brake lights not working"
],

"questions":[
{
"id":"q1",
"text":"Brake dabane pe rear light ON nahi hoti?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Brake light kabhi kaam karti hai kabhi nahi?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check brake lights when pedal pressed"
],

"repair_cost":{"min":800,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":50,
"problem":"Sunroof Drain Blocked",
"system":"body",
"component":"sunroof drain",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"water leakage inside cabin"
],

"questions":[
{
"id":"q1",
"text":"Car ke andar paani aa raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Sunroof ke paas leakage dikh raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect sunroof drain outlets"
],

"repair_cost":{"min":1000,"max":4000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":51,
"problem":"Power Steering Fluid Low",
"system":"steering",
"component":"power steering system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"hard steering",
"whining noise while turning"
],

"questions":[
{
"id":"q1",
"text":"Steering heavy ho gaya hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Turn karte waqt whining sound aati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check power steering fluid level"
],

"repair_cost":{"min":500,"max":4000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":52,
"problem":"Power Steering Pump Failure",
"system":"steering",
"component":"power steering pump",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"hard steering",
"whining noise from pump"
],

"questions":[
{
"id":"q1",
"text":"Steering bohot heavy ho gaya hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Pump side se loud noise aa rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe steering effort during turns"
],

"repair_cost":{"min":4000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":53,
"problem":"Steering Rack Wear",
"system":"steering",
"component":"steering rack",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"loose steering",
"steering knocking noise"
],

"questions":[
{
"id":"q1",
"text":"Steering loose lag raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Steering me knock ya play feel ho raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check steering free play"
],

"repair_cost":{"min":8000,"max":35000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":54,
"problem":"Tie Rod End Wear",
"system":"steering",
"component":"tie rod",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"car pulling to one side",
"steering loose",
"steering vibration"
],

"questions":[
{
"id":"q1",
"text":"Steering loose ya unstable lag raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Car ek side pull kar rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect steering play"
],

"repair_cost":{"min":2500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":55,
"problem":"Steering Column Joint Wear",
"system":"steering",
"component":"steering column joint",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"steering vibration",
"knocking in steering"
],

"questions":[
{
"id":"q1",
"text":"Steering me vibration feel ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Turning pe knock feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe steering vibration while driving"
],

"repair_cost":{"min":3000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":56,
"problem":"Catalytic Converter Blocked",
"system":"exhaust",
"component":"catalytic converter",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"engine power loss",
"poor fuel efficiency"
],

"questions":[
{
"id":"q1",
"text":"Car ki power kam ho gayi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Mileage bhi kam ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check exhaust flow"
],

"repair_cost":{"min":8000,"max":35000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":57,
"problem":"Exhaust Leak",
"system":"exhaust",
"component":"exhaust pipe",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"loud exhaust noise",
"exhaust smell"
],

"questions":[
{
"id":"q1",
"text":"Car se loud awaaz aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Exhaust smell feel ho rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect exhaust pipe for leak"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":58,
"problem":"Muffler Damage",
"system":"exhaust",
"component":"muffler",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"loud exhaust sound",
"vibration from rear"
],

"questions":[
{
"id":"q1",
"text":"Rear side se loud sound aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Car ke peeche vibration feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect muffler condition"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":59,
"problem":"DPF Filter Blocked",
"system":"exhaust",
"component":"diesel particulate filter",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"DPF warning light",
"engine power reduced"
],

"questions":[
{
"id":"q1",
"text":"DPF warning light ON hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Car ki power suddenly kam ho gayi?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check DPF warning indicator"
],

"repair_cost":{"min":5000,"max":25000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":60,
"problem":"EGR Valve Blocked",
"system":"engine",
"component":"EGR valve",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"rough idle",
"engine hesitation"
],

"questions":[
{
"id":"q1",
"text":"Idle pe engine smooth nahi chal raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration pe hesitation feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":2500,"max":7000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":61,
"problem":"Crankshaft Position Sensor Fault",
"system":"engine",
"component":"crankshaft position sensor",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine not starting",
"engine stalling"
],

"questions":[
{
"id":"q1",
"text":"Car start nahi ho rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine chalte-chalte band ho jata hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":2500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":62,
"problem":"Camshaft Position Sensor Fault",
"system":"engine",
"component":"camshaft position sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine misfire",
"poor acceleration"
],

"questions":[
{
"id":"q1",
"text":"Engine misfire feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration smooth nahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":2500,"max":9000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":63,
"problem":"Throttle Position Sensor Fault",
"system":"engine",
"component":"throttle position sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine hesitation",
"irregular acceleration"
],

"questions":[
{
"id":"q1",
"text":"Acceleration irregular lag raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Throttle response delayed hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":3000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":64,
"problem":"Knock Sensor Fault",
"system":"engine",
"component":"knock sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"engine knocking sound",
"reduced engine power"
],

"questions":[
{
"id":"q1",
"text":"Engine knocking sound aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Power kam feel ho rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":3000,"max":9000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":65,
"problem":"Idle Air Control Valve Fault",
"system":"engine",
"component":"idle air control valve",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine idle unstable",
"RPM fluctuating"
],

"questions":[
{
"id":"q1",
"text":"Idle pe RPM up-down ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Car khadi hone pe engine stable nahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe idle RPM"
],

"repair_cost":{"min":2000,"max":7000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":66,
"problem":"Drive Belt Worn",
"system":"engine",
"component":"drive belt",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"squealing noise from engine"
],

"questions":[
{
"id":"q1",
"text":"Engine se squealing sound aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Cold start pe noise zyada hoti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect belt condition"
],

"repair_cost":{"min":800,"max":4000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":67,
"problem":"Serpentine Belt Slipping",
"system":"engine",
"component":"serpentine belt",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"squealing noise during acceleration"
],

"questions":[
{
"id":"q1",
"text":"Acceleration pe squealing sound aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Wet condition me noise zyada hoti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check belt tension"
],

"repair_cost":{"min":1000,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":68,
"problem":"Transmission Mount Worn",
"system":"transmission",
"component":"transmission mount",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"vibration during gear shift"
],

"questions":[
{
"id":"q1",
"text":"Gear change pe vibration feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration pe thud feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect drivetrain movement"
],

"repair_cost":{"min":3000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":69,
"problem":"Clutch Release Bearing Worn",
"system":"transmission",
"component":"clutch release bearing",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"whining noise when clutch pressed"
],

"questions":[
{
"id":"q1",
"text":"Clutch dabane pe whining sound aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Clutch chhodne pe sound band ho jati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"listen for noise when clutch pedal pressed"
],

"repair_cost":{"min":5000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":70,
"problem":"Wheel Balancing Incorrect",
"system":"suspension",
"component":"wheel balancing",
"severity":"low",
"urgency":"service_soon",
"probability":7,

"symptoms":[
"car shaking while driving",
"steering vibration"
],

"questions":[
{
"id":"q1",
"text":"80–100 speed pe vibration feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Steering shake karta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe vibration around 80-100 km/h"
],

"repair_cost":{"min":500,"max":2000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":71,
"problem":"Tire Sidewall Damage",
"system":"suspension",
"component":"tire",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"bulge on tire sidewall"
],

"questions":[
{
"id":"q1",
"text":"Tyre pe bulge ya phoola hua part hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Driving unsafe feel ho rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect tire sidewall"
],

"repair_cost":{"min":3000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":72,
"problem":"Wheel Rim Bent",
"system":"suspension",
"component":"wheel rim",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"steering vibration",
"air pressure loss"
],

"questions":[
{
"id":"q1",
"text":"Tyre me bar-bar air kam ho rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Steering vibration feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect wheel rim"
],

"repair_cost":{"min":2000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":73,
"problem":"Parking Brake Stuck",
"system":"brake",
"component":"parking brake",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"car not moving freely"
],

"questions":[
{
"id":"q1",
"text":"Car freely roll nahi kar rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Parking brake release ke baad bhi tight lag rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check parking brake release"
],

"repair_cost":{"min":1000,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":74,
"problem":"Door Lock Actuator Failure",
"system":"body",
"component":"door lock actuator",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"door not locking or unlocking"
],

"questions":[
{
"id":"q1",
"text":"Door lock/unlock kaam nahi kar raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Central locking fail ho raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"test central locking"
],

"repair_cost":{"min":1500,"max":6000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":75,
"problem":"Window Regulator Failure",
"system":"body",
"component":"window regulator",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"window not moving"
],

"questions":[
{
"id":"q1",
"text":"Window upar-niche nahi ho rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Switch dabane pe koi response nahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"test window switch"
],

"repair_cost":{"min":2000,"max":7000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":76,
"problem":"ECU Communication Error",
"system":"electrical",
"component":"ECU",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"multiple warning lights",
"engine performance irregular"
],

"questions":[
{
"id":"q1",
"text":"Dashboard pe multiple warning lights aa rahi hain?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Car ka behavior abnormal ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":3000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":77,
"problem":"ABS Module Failure",
"system":"brake",
"component":"ABS module",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"ABS warning light",
"ABS not working"
],

"questions":[
{
"id":"q1",
"text":"ABS light ON hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Hard braking pe ABS activate nahi ho raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan ABS system codes"
],

"repair_cost":{"min":6000,"max":25000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":78,
"problem":"Instrument Cluster Fault",
"system":"electrical",
"component":"instrument cluster",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"speedometer not working",
"dashboard display flickering"
],

"questions":[
{
"id":"q1",
"text":"Speedometer kaam nahi kar raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Dashboard flicker ho raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe dashboard display behavior"
],

"repair_cost":{"min":4000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":79,
"problem":"Central Locking Module Failure",
"system":"electrical",
"component":"central locking system",
"severity":"low",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"central locking not responding"
],

"questions":[
{
"id":"q1",
"text":"Central locking kaam nahi kar raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"All doors ek saath lock nahi ho rahe?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"test central locking using key"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":80,
"problem":"Key Fob Battery Dead",
"system":"electrical",
"component":"key fob",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"car not responding to key",
"remote not working"
],

"questions":[
{
"id":"q1",
"text":"Remote se car unlock nahi ho rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Key button dabane pe response nahi mil raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"replace key fob battery"
],

"repair_cost":{"min":100,"max":500},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":81,
"problem":"Heater Core Blocked",
"system":"cooling",
"component":"heater core",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"heater not producing heat",
"fogging inside windshield"
],

"questions":[
{
"id":"q1",
"text":"Heater se garam hawa nahi aa rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Windshield fog ho rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check heater performance"
],

"repair_cost":{"min":3000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":82,
"problem":"Cooling Fan Relay Failure",
"system":"cooling",
"component":"fan relay",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"radiator fan not working",
"engine overheating in traffic"
],

"questions":[
{
"id":"q1",
"text":"Fan bilkul ON nahi ho raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Traffic me overheating ho rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect fan relay"
],

"repair_cost":{"min":1000,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":83,
"problem":"Coolant Temperature Sensor Fault",
"system":"cooling",
"component":"temperature sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"incorrect temperature reading",
"engine overheating warning"
],

"questions":[
{
"id":"q1",
"text":"Temperature reading incorrect lag rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Warning bina reason ke aa rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD temperature data"
],

"repair_cost":{"min":2000,"max":7000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":84,
"problem":"Coolant Hose Leak",
"system":"cooling",
"component":"coolant hose",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"coolant leakage",
"engine overheating"
],

"questions":[
{
"id":"q1",
"text":"Coolant leak dikh raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine heat zyada ho raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect hoses for leaks"
],

"repair_cost":{"min":800,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":85,
"problem":"Radiator Cap Failure",
"system":"cooling",
"component":"radiator cap",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"coolant loss",
"engine overheating"
],

"questions":[
{
"id":"q1",
"text":"Coolant level bar-bar kam ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Radiator cap loose ya faulty lag raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect radiator cap seal"
],

"repair_cost":{"min":300,"max":1500},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":86,
"problem":"Seat Belt Sensor Fault",
"system":"electrical",
"component":"seat belt sensor",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"seat belt warning stays on"
],

"questions":[
{
"id":"q1",
"text":"Seat belt lagane ke baad bhi warning aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Sensor error lag raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check seat belt latch"
],

"repair_cost":{"min":1000,"max":4000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":87,
"problem":"Reverse Camera Failure",
"system":"electrical",
"component":"reverse camera",
"severity":"low",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"no rear camera display"
],

"questions":[
{
"id":"q1",
"text":"Reverse camera display nahi aa raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Screen black ho jati hai reverse me?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check infotainment display"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":88,
"problem":"Infotainment System Freeze",
"system":"electrical",
"component":"infotainment system",
"severity":"low",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"screen freezing",
"touchscreen not responding"
],

"questions":[
{
"id":"q1",
"text":"Screen freeze ho jati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Touch kaam nahi karta?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"restart infotainment system"
],

"repair_cost":{"min":3000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":89,
"problem":"Interior Cabin Water Leak",
"system":"body",
"component":"body seals",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"water inside cabin",
"wet floor carpet"
],

"questions":[
{
"id":"q1",
"text":"Car ke andar paani aa raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Floor carpet wet hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect door seals"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":90,
"problem":"Door Hinge Wear",
"system":"body",
"component":"door hinge",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"door sagging",
"door noise while opening"
],

"questions":[
{
"id":"q1",
"text":"Door properly close nahi ho raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Door open/close pe noise aati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check door alignment"
],

"repair_cost":{"min":1000,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":91,
"problem":"Airbag Warning Light",
"system":"safety",
"component":"airbag system",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"airbag warning light on"
],

"questions":[
{
"id":"q1",
"text":"Airbag warning light ON hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Recent me accident ya repair hua hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan airbag system codes"
],

"repair_cost":{"min":3000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":92,
"problem":"Seat Occupancy Sensor Fault",
"system":"safety",
"component":"seat sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"airbag light on"
],

"questions":[
{
"id":"q1",
"text":"Seat pe koi nahi hai phir bhi warning aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Passenger seat sensor error lag raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":3000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":93,
"problem":"Parking Sensor Failure",
"system":"safety",
"component":"parking sensor",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"parking sensor not beeping"
],

"questions":[
{
"id":"q1",
"text":"Reverse me sensor beep nahi kar raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Obstacle hone ke baad bhi alert nahi mil raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check sensor obstruction"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":94,
"problem":"ADAS Camera Misalignment",
"system":"safety",
"component":"ADAS camera",
"severity":"medium",
"urgency":"service_soon",
"probability":2,

"symptoms":[
"lane assist not working"
],

"questions":[
{
"id":"q1",
"text":"Lane assist kaam nahi kar raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Windshield pe dirt ya obstruction hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"clean windshield camera area"
],

"repair_cost":{"min":5000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":95,
"problem":"Blind Spot Sensor Fault",
"system":"safety",
"component":"blind spot sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":2,

"symptoms":[
"blind spot warning not working"
],

"questions":[
{
"id":"q1",
"text":"Blind spot alert kaam nahi kar raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Side sensors clean hain?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect sensor area"
],

"repair_cost":{"min":6000,"max":25000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":96,
"problem":"Cruise Control Not Working",
"system":"electrical",
"component":"cruise control system",
"severity":"low",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"cruise control not activating"
],

"questions":[
{
"id":"q1",
"text":"Cruise control ON nahi ho raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Speed set nahi ho rahi?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check cruise control switch"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":97,
"problem":"Fuel Gauge Incorrect Reading",
"system":"electrical",
"component":"fuel gauge sensor",
"severity":"low",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"fuel gauge inaccurate"
],

"questions":[
{
"id":"q1",
"text":"Fuel gauge wrong reading dikha raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Fuel suddenly drop ya increase dikhata hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe fuel level changes"
],

"repair_cost":{"min":3000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":98,
"problem":"Speed Sensor Failure",
"system":"electrical",
"component":"speed sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"speedometer not working"
],

"questions":[
{
"id":"q1",
"text":"Speedometer kaam nahi kar raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Speed reading incorrect hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":2500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":99,
"problem":"Alternator Belt Loose",
"system":"engine",
"component":"drive belt",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"squealing noise from engine"
],

"questions":[
{
"id":"q1",
"text":"Engine se belt wali awaaz aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration pe noise badh jati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect belt tension"
],

"repair_cost":{"min":800,"max":4000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":100,
"problem":"Engine Head Gasket Leak",
"system":"engine",
"component":"head gasket",
"severity":"critical",
"urgency":"stop_driving",
"probability":2,

"symptoms":[
"white smoke from exhaust",
"coolant loss",
"engine overheating"
],

"questions":[
{
"id":"q1",
"text":"Exhaust se white smoke aa raha hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Coolant rapidly kam ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check coolant level frequently"
],

"repair_cost":{"min":20000,"max":60000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":101,
"problem":"Turbocharger Lag",
"system":"engine",
"component":"turbocharger",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"delay in acceleration",
"low power at low RPM"
],

"questions":[
{
"id":"q1",
"text":"Acceleration me delay feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Low RPM pe power kam lagti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe turbo response"
],

"repair_cost":{"min":5000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":102,
"problem":"Turbocharger Oil Leak",
"system":"engine",
"component":"turbocharger",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"blue smoke from exhaust",
"oil consumption high"
],

"questions":[
{
"id":"q1",
"text":"Exhaust se blue smoke aa raha hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Engine oil jaldi kam ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check oil level frequently"
],

"repair_cost":{"min":10000,"max":40000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":103,
"problem":"Intercooler Leak",
"system":"engine",
"component":"intercooler",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"loss of turbo pressure",
"reduced engine power"
],

"questions":[
{
"id":"q1",
"text":"Turbo power kam ho gayi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration weak lag raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect intercooler pipes"
],

"repair_cost":{"min":3000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":104,
"problem":"Mass Air Flow Sensor Dirty",
"system":"engine",
"component":"MAF sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"poor acceleration",
"rough idle",
"poor fuel economy"
],

"questions":[
{
"id":"q1",
"text":"Acceleration smooth nahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Mileage kam ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"clean MAF sensor"
],

"repair_cost":{"min":1500,"max":6000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":105,
"problem":"Oxygen Sensor Fault",
"system":"engine",
"component":"O2 sensor",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"check engine light",
"poor fuel economy"
],

"questions":[
{
"id":"q1",
"text":"Check engine light ON hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Mileage kam ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":2000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":106,
"problem":"Engine Mount Worn",
"system":"engine",
"component":"engine mount",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine vibration",
"jerk during acceleration"
],

"questions":[
{
"id":"q1",
"text":"Engine vibration zyada feel ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration pe jerk feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe engine movement"
],

"repair_cost":{"min":3000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":107,
"problem":"Flywheel Damage",
"system":"engine",
"component":"flywheel",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"engine vibration",
"clutch engagement issues"
],

"questions":[
{
"id":"q1",
"text":"Clutch chhodte time vibration feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Gear engage karte waqt jerk feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe clutch engagement"
],

"repair_cost":{"min":8000,"max":30000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":108,
"problem":"Timing Chain Noise",
"system":"engine",
"component":"timing chain",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"rattling noise from engine"
],

"questions":[
{
"id":"q1",
"text":"Engine se rattling sound aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Cold start pe noise zyada hoti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"listen during cold start"
],

"repair_cost":{"min":8000,"max":25000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":109,
"problem":"Timing Belt Worn",
"system":"engine",
"component":"timing belt",
"severity":"critical",
"urgency":"stop_driving",
"probability":2,

"symptoms":[
"engine noise",
"engine misfire"
],

"questions":[
{
"id":"q1",
"text":"Timing belt service due hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine se abnormal noise aa rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check service history"
],

"repair_cost":{"min":5000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":110,
"problem":"Spark Plug Fouled",
"system":"engine",
"component":"spark plug",
"severity":"medium",
"urgency":"service_soon",
"probability":6,

"symptoms":[
"engine misfire",
"rough idle",
"poor fuel economy"
],

"questions":[
{
"id":"q1",
"text":"Engine misfire feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Idle smooth nahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect spark plugs"
],

"repair_cost":{"min":800,"max":4000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":111,
"problem":"Ignition Coil Failure",
"system":"engine",
"component":"ignition coil",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"engine misfire",
"loss of power"
],

"questions":[
{
"id":"q1",
"text":"Acceleration pe power loss feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine shake karta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":2000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":112,
"problem":"Fuel Injector Clogged",
"system":"fuel",
"component":"fuel injector",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"engine hesitation",
"poor fuel economy"
],

"questions":[
{
"id":"q1",
"text":"Acceleration smooth nahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Mileage kam ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"use injector cleaner"
],

"repair_cost":{"min":2000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":113,
"problem":"Fuel Injector Leak",
"system":"fuel",
"component":"fuel injector",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"fuel smell",
"poor mileage"
],

"questions":[
{
"id":"q1",
"text":"Fuel smell aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Mileage suddenly drop hua hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect injector area"
],

"repair_cost":{"min":4000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":114,
"problem":"Throttle Body Dirty",
"system":"engine",
"component":"throttle body",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"rough idle",
"engine hesitation"
],

"questions":[
{
"id":"q1",
"text":"Idle pe engine rough chal raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration delay feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"clean throttle body"
],

"repair_cost":{"min":1000,"max":4000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":115,
"problem":"Vacuum Leak",
"system":"engine",
"component":"vacuum lines",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"high idle",
"engine hesitation"
],

"questions":[
{
"id":"q1",
"text":"Idle RPM zyada hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine response unstable hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect vacuum hoses"
],

"repair_cost":{"min":800,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":116,
"problem":"PCV Valve Blocked",
"system":"engine",
"component":"PCV valve",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"oil consumption high",
"engine rough"
],

"questions":[
{
"id":"q1",
"text":"Engine oil jaldi kam ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine rough chal raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check PCV valve"
],

"repair_cost":{"min":800,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":117,
"problem":"Radiator Fan Noise",
"system":"cooling",
"component":"radiator fan",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"loud fan noise"
],

"questions":[
{
"id":"q1",
"text":"Fan se loud noise aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine garam hone pe noise badh jati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect fan blades"
],

"repair_cost":{"min":1500,"max":6000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":118,
"problem":"Coolant Mixed With Oil",
"system":"engine",
"component":"head gasket",
"severity":"critical",
"urgency":"stop_driving",
"probability":2,

"symptoms":[
"milky oil",
"engine overheating"
],

"questions":[
{
"id":"q1",
"text":"Engine oil milky ho gaya hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Engine overheat bhi ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check oil cap for milky residue"
],

"repair_cost":{"min":20000,"max":70000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":119,
"problem":"Engine Seized",
"system":"engine",
"component":"engine",
"severity":"critical",
"urgency":"stop_driving",
"probability":1,

"symptoms":[
"engine not turning",
"loud knock before failure"
],

"questions":[
{
"id":"q1",
"text":"Engine bilkul crank nahi ho raha?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Failure se pehle loud knock suna tha?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"try manual crank"
],

"repair_cost":{"min":40000,"max":150000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":120,
"problem":"Battery Dead",
"system":"electrical",
"component":"battery",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"car not starting",
"no dashboard lights"
],

"questions":[
{
"id":"q1",
"text":"Car start nahi ho rahi aur lights bhi off hain?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Battery purani hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"try jump start"
],

"repair_cost":{"min":3000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":131,
"problem":"Car Pulling Under Acceleration",
"system":"drivetrain",
"component":"alignment/drive system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"car pulling while accelerating"
],

"questions":[
{
"id":"q1",
"text":"Acceleration pe car ek side ja rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Steering seedha rakhne par bhi drift hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check alignment and tire pressure"
],

"repair_cost":{"min":800,"max":4000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":132,
"problem":"Car Pulling Under Braking",
"system":"brake",
"component":"brake system",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"car pulling while braking"
],

"questions":[
{
"id":"q1",
"text":"Brake lagate waqt car ek side khich rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Brake uneven feel ho raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect brake pads and calipers"
],

"repair_cost":{"min":2000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":133,
"problem":"Car Vibrates at Idle",
"system":"engine",
"component":"engine mount / ignition",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"vibration at idle"
],

"questions":[
{
"id":"q1",
"text":"Car idle pe vibrate karti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"AC ON hone par vibration badh jata hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe vibration at idle"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":134,
"problem":"Car Jerks While Driving",
"system":"engine",
"component":"fuel/ignition",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"jerks during driving"
],

"questions":[
{
"id":"q1",
"text":"Driving ke time jerk feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration smooth nahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe acceleration pattern"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":135,
"problem":"Car Stalls Frequently",
"system":"engine",
"component":"fuel/air system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine stalls frequently"
],

"questions":[
{
"id":"q1",
"text":"Car chalte-chalte band ho jati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Restart karne me problem hoti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe stall conditions"
],

"repair_cost":{"min":3000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":136,
"problem":"Hard Starting Cold Engine",
"system":"engine",
"component":"fuel/ignition",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"hard start in morning"
],

"questions":[
{
"id":"q1",
"text":"Subah car start karna mushkil hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Multiple self lagani padti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe cold start behavior"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":137,
"problem":"Hard Starting Hot Engine",
"system":"engine",
"component":"fuel system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"hard start after driving"
],

"questions":[
{
"id":"q1",
"text":"Engine garam hone ke baad start problem hoti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Cold start normal hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe hot restart"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":138,
"problem":"Steering Returns Slowly",
"system":"steering",
"component":"steering system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"steering not returning"
],

"questions":[
{
"id":"q1",
"text":"Turn ke baad steering apne aap seedha nahi hota?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Steering heavy lagta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe steering return"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":139,
"problem":"Steering Noise While Turning",
"system":"steering",
"component":"steering system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"noise while turning"
],

"questions":[
{
"id":"q1",
"text":"Steering turn karte waqt awaaz aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Low speed pe noise zyada hoti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"turn steering fully both sides"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":140,
"problem":"Clutch Pedal Hard",
"system":"transmission",
"component":"clutch system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"hard clutch pedal"
],

"questions":[
{
"id":"q1",
"text":"Clutch pedal hard ho gaya hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Traffic me clutch use karna difficult ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check clutch cable/hydraulic system"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":141,
"problem":"Clutch Pedal Soft",
"system":"transmission",
"component":"clutch system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"soft clutch pedal",
"gear shifting issues"
],

"questions":[
{
"id":"q1",
"text":"Clutch pedal soft lag raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Gear shift me problem ho rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check clutch fluid"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":142,
"problem":"Gear Slipping",
"system":"transmission",
"component":"gearbox",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"gear slipping during driving"
],

"questions":[
{
"id":"q1",
"text":"Driving ke time gear slip ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"RPM badh raha hai lekin speed nahi badh rahi?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe RPM vs speed"
],

"repair_cost":{"min":8000,"max":40000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":143,
"problem":"Gear Not Engaging",
"system":"transmission",
"component":"gearbox",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"gear not engaging"
],

"questions":[
{
"id":"q1",
"text":"Gear lag nahi raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Clutch dabane ke baad bhi gear nahi lagta?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"test gear engagement"
],

"repair_cost":{"min":5000,"max":30000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":144,
"problem":"Delayed Gear Shift Automatic",
"system":"transmission",
"component":"automatic gearbox",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"delayed gear shifts"
],

"questions":[
{
"id":"q1",
"text":"Gear shift delay ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration smooth nahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe shift timing"
],

"repair_cost":{"min":4000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":145,
"problem":"Car Not Moving In Gear",
"system":"transmission",
"component":"clutch/gearbox",
"severity":"critical",
"urgency":"stop_driving",
"probability":3,

"symptoms":[
"car not moving in gear"
],

"questions":[
{
"id":"q1",
"text":"Gear lagane ke baad bhi car move nahi kar rahi?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Engine RPM badh raha hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check clutch slipping"
],

"repair_cost":{"min":8000,"max":40000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":146,
"problem":"Hybrid Battery Degradation",
"system":"hybrid",
"component":"battery pack",
"severity":"high",
"urgency":"service_soon",
"probability":2,

"symptoms":[
"reduced hybrid efficiency",
"battery warning"
],

"questions":[
{
"id":"q1",
"text":"Hybrid mileage kam ho gaya hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Battery warning aa rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan hybrid battery health"
],

"repair_cost":{"min":20000,"max":100000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":147,
"problem":"Regenerative Braking Not Working",
"system":"hybrid",
"component":"regen system",
"severity":"medium",
"urgency":"service_soon",
"probability":2,

"symptoms":[
"regen braking not active"
],

"questions":[
{
"id":"q1",
"text":"Regenerative braking feel nahi ho rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Battery charge increase nahi ho raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe regen indicator"
],

"repair_cost":{"min":5000,"max":30000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":148,
"problem":"Electric Power Steering Failure",
"system":"steering",
"component":"EPS system",
"severity":"high",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"steering suddenly heavy"
],

"questions":[
{
"id":"q1",
"text":"Steering suddenly heavy ho gaya?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"EPS warning light ON hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan EPS system"
],

"repair_cost":{"min":8000,"max":40000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":149,
"problem":"Start-Stop System Not Working",
"system":"electrical",
"component":"start-stop system",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"start-stop inactive"
],

"questions":[
{
"id":"q1",
"text":"Start-stop feature kaam nahi kar raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Battery weak lag rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check battery condition"
],

"repair_cost":{"min":1000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":150,
"problem":"Car Overheats In Traffic Only",
"system":"cooling",
"component":"fan/cooling system",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"overheating in traffic",
"normal on highway"
],

"questions":[
{
"id":"q1",
"text":"Sirf traffic me overheat hoti hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"High speed pe normal ho jati hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check radiator fan operation"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":161,
"problem":"Engine Overheating On Highway",
"system":"cooling",
"component":"radiator/cooling system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"overheating at high speed"
],

"questions":[
{
"id":"q1",
"text":"Highway pe overheating hoti hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Traffic me normal rehti hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"inspect radiator blockage"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":162,
"problem":"Car Loses Power On Incline",
"system":"engine",
"component":"fuel/air system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"power loss uphill"
],

"questions":[
{
"id":"q1",
"text":"Chadhai pe power kam ho jati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Flat road pe normal hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"test power on incline"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":163,
"problem":"Black Smoke From Exhaust",
"system":"engine",
"component":"fuel system",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"black smoke"
],

"questions":[
{
"id":"q1",
"text":"Exhaust se kala dhua aa raha hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Fuel consumption badh gaya hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check air filter and injectors"
],

"repair_cost":{"min":2000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":164,
"problem":"White Smoke From Exhaust",
"system":"engine",
"component":"cooling/head gasket",
"severity":"critical",
"urgency":"stop_driving",
"probability":4,

"symptoms":[
"white smoke"
],

"questions":[
{
"id":"q1",
"text":"White smoke continuously aa raha hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Coolant kam ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check coolant level"
],

"repair_cost":{"min":20000,"max":70000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":165,
"problem":"Blue Smoke From Exhaust",
"system":"engine",
"component":"engine oil system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"blue smoke"
],

"questions":[
{
"id":"q1",
"text":"Blue smoke aa raha hai exhaust se?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Engine oil kam ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check oil consumption"
],

"repair_cost":{"min":5000,"max":40000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":166,
"problem":"Engine Backfire",
"system":"engine",
"component":"fuel/ignition",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"backfire sound"
],

"questions":[
{
"id":"q1",
"text":"Exhaust se phat jaisi awaaz aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration pe issue hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check ignition timing"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":167,
"problem":"Engine Knocking Under Load",
"system":"engine",
"component":"combustion system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"knocking under load"
],

"questions":[
{
"id":"q1",
"text":"Load pe engine knock karta hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Acceleration pe metallic sound aati hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"use high octane fuel test"
],

"repair_cost":{"min":3000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":168,
"problem":"Fuel Smell Inside Cabin",
"system":"fuel",
"component":"fuel line",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"fuel smell inside cabin"
],

"questions":[
{
"id":"q1",
"text":"Car ke andar fuel smell aa rahi hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Leak ka doubt hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"inspect fuel lines"
],

"repair_cost":{"min":2000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":169,
"problem":"Brake Pedal Goes To Floor",
"system":"brake",
"component":"brake system",
"severity":"critical",
"urgency":"stop_driving",
"probability":5,

"symptoms":[
"brake pedal sinking"
],

"questions":[
{
"id":"q1",
"text":"Brake pedal floor tak ja raha hai?",
"impact":{"yes":1.7,"no":0.4}
},
{
"id":"q2",
"text":"Braking weak ho gayi hai?",
"impact":{"yes":1.6,"no":0.5}
}
],

"user_checks":[
"check brake fluid leakage"
],

"repair_cost":{"min":3000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":170,
"problem":"Brake Pedal Vibrates",
"system":"brake",
"component":"brake disc",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"vibration while braking"
],

"questions":[
{
"id":"q1",
"text":"Brake lagate waqt pedal vibrate karta hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"High speed braking pe vibration zyada hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check brake discs"
],

"repair_cost":{"min":4000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":171,
"problem":"Handbrake Not Holding",
"system":"brake",
"component":"parking brake",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"handbrake ineffective"
],

"questions":[
{
"id":"q1",
"text":"Handbrake lagane ke baad bhi car move hoti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Slope pe hold nahi karti?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"test on slope"
],

"repair_cost":{"min":1500,"max":6000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":172,
"problem":"AC Cooling Drops After Some Time",
"system":"ac",
"component":"compressor/condenser",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"cooling reduces after running"
],

"questions":[
{
"id":"q1",
"text":"AC start me thanda hai phir kam ho jata hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Long drive me cooling drop hoti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe AC after 15 min"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":173,
"problem":"AC Smells Bad",
"system":"ac",
"component":"cabin filter/evaporator",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"bad smell from AC"
],

"questions":[
{
"id":"q1",
"text":"AC se bad smell aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"AC on karte hi smell aati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"replace cabin filter"
],

"repair_cost":{"min":500,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":174,
"problem":"AC Cooling Uneven",
"system":"ac",
"component":"air distribution",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"uneven cooling"
],

"questions":[
{
"id":"q1",
"text":"Ek side thandi aur dusri side garam hawa aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Rear AC weak hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check vents and airflow"
],

"repair_cost":{"min":1000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":175,
"problem":"Car Feels Underpowered",
"system":"engine",
"component":"engine system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"low power overall"
],

"questions":[
{
"id":"q1",
"text":"Car overall slow lag rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration weak hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check air filter"
],

"repair_cost":{"min":1000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":176,
"problem":"Mileage Suddenly Dropped",
"system":"engine",
"component":"fuel system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"low mileage"
],

"questions":[
{
"id":"q1",
"text":"Mileage suddenly kam ho gaya hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Driving pattern same hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check tire pressure"
],

"repair_cost":{"min":500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":177,
"problem":"Engine Oil Burning",
"system":"engine",
"component":"engine internals",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"oil level dropping"
],

"questions":[
{
"id":"q1",
"text":"Engine oil bar-bar kam ho raha hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Blue smoke aa raha hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check oil level weekly"
],

"repair_cost":{"min":5000,"max":40000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":178,
"problem":"Engine Oil Leak",
"system":"engine",
"component":"engine seals",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"oil leak under car"
],

"questions":[
{
"id":"q1",
"text":"Car ke niche oil leak dikh raha hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Engine oil level kam ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"inspect under engine"
],

"repair_cost":{"min":1000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":179,
"problem":"Coolant Leak Visible",
"system":"cooling",
"component":"cooling system",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"coolant leak"
],

"questions":[
{
"id":"q1",
"text":"Coolant leak clearly dikh raha hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Engine heat bhi ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check radiator and hoses"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":180,
"problem":"Radiator Blocked Internal",
"system":"cooling",
"component":"radiator",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"overheating",
"poor cooling efficiency"
],

"questions":[
{
"id":"q1",
"text":"Engine normal se zyada heat ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Coolant level theek hone ke baad bhi issue hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"flush radiator"
],

"repair_cost":{"min":3000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":181,
"problem":"Engine Misfire Under Load",
"system":"engine",
"component":"ignition/fuel",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"misfire under load"
],

"questions":[
{
"id":"q1",
"text":"Acceleration pe engine misfire karta hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Load badhne pe problem badhti hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"scan misfire codes"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":182,
"problem":"Rough Idle After Warm Up",
"system":"engine",
"component":"fuel/air",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"rough idle after warm"
],

"questions":[
{
"id":"q1",
"text":"Engine garam hone ke baad idle rough ho jata hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Cold start me smooth hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe idle behavior"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":183,
"problem":"Battery Drains Overnight",
"system":"electrical",
"component":"battery/drain",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"battery dead next day"
],

"questions":[
{
"id":"q1",
"text":"Raat me battery discharge ho jati hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Next day car start nahi hoti?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check parasitic drain"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":184,
"problem":"Starter Click But No Crank",
"system":"electrical",
"component":"starter motor",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"clicking sound no crank"
],

"questions":[
{
"id":"q1",
"text":"Click sound aati hai but engine crank nahi hota?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Battery theek lag rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check starter motor"
],

"repair_cost":{"min":4000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":185,
"problem":"Engine Cranks But No Start",
"system":"engine",
"component":"fuel/ignition",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"crank but no start"
],

"questions":[
{
"id":"q1",
"text":"Engine crank ho raha hai but start nahi ho raha?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Fuel ya ignition issue lag raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check fuel pump and spark"
],

"repair_cost":{"min":2000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":186,
"problem":"Check Engine Light Flashing",
"system":"engine",
"component":"engine system",
"severity":"critical",
"urgency":"stop_driving",
"probability":5,

"symptoms":[
"flashing check engine light"
],

"questions":[
{
"id":"q1",
"text":"Check engine light blink kar rahi hai?",
"impact":{"yes":1.7,"no":0.4}
},
{
"id":"q2",
"text":"Engine misfire feel ho raha hai?",
"impact":{"yes":1.6,"no":0.5}
}
],

"user_checks":[
"stop driving immediately"
],

"repair_cost":{"min":3000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":187,
"problem":"Check Engine Light Solid",
"system":"engine",
"component":"engine system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"solid check engine light"
],

"questions":[
{
"id":"q1",
"text":"Check engine light continuously ON hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Car normal chal rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":1000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":188,
"problem":"Car Feels Sluggish",
"system":"engine",
"component":"engine system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"slow response"
],

"questions":[
{
"id":"q1",
"text":"Car sluggish lag rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration me delay hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check air filter"
],

"repair_cost":{"min":1000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":189,
"problem":"Engine Vibrates At High Speed",
"system":"engine",
"component":"engine/drivetrain",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"vibration at high speed"
],

"questions":[
{
"id":"q1",
"text":"High speed pe vibration feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Speed badhne par vibration badhta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe speed vibration"
],

"repair_cost":{"min":1500,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":190,
"problem":"Car Hesitates On Acceleration",
"system":"engine",
"component":"fuel/air system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"hesitation on acceleration"
],

"questions":[
{
"id":"q1",
"text":"Acceleration pe hesitation feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Throttle response slow hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe throttle response"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":191,
"problem":"Car Feels Heavy To Drive",
"system":"engine",
"component":"engine/drivetrain",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"heavy driving feel"
],

"questions":[
{
"id":"q1",
"text":"Car heavy feel ho rahi hai drive karte waqt?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration weak lag raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check tire pressure"
],

"repair_cost":{"min":500,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":192,
"problem":"Engine Overheats With AC ON",
"system":"cooling",
"component":"cooling system",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"overheat with AC"
],

"questions":[
{
"id":"q1",
"text":"AC ON karte hi overheating hoti hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"AC OFF karne par normal ho jata hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check radiator fan load"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":193,
"problem":"Car Overheats With Full Load",
"system":"cooling",
"component":"engine cooling",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"overheat with load"
],

"questions":[
{
"id":"q1",
"text":"Full load pe overheating hoti hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Normal drive me issue nahi hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"test under load"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":194,
"problem":"Car Overheats On Uphill",
"system":"cooling",
"component":"cooling system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"overheat uphill"
],

"questions":[
{
"id":"q1",
"text":"Chadhai pe overheating hoti hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Flat road pe normal hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check coolant flow"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":195,
"problem":"Brake Noise While Driving",
"system":"brake",
"component":"brake system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"brake noise"
],

"questions":[
{
"id":"q1",
"text":"Brake use karte waqt noise aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Driving me bhi sound aati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"inspect brake pads"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":196,
"problem":"Brake Smell Burning",
"system":"brake",
"component":"brake system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"burning smell from brakes"
],

"questions":[
{
"id":"q1",
"text":"Brake se burning smell aa rahi hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Heavy braking ke baad smell aati hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check brake overheating"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":197,
"problem":"Car Shakes While Braking",
"system":"brake",
"component":"brake disc",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"shaking while braking"
],

"questions":[
{
"id":"q1",
"text":"Brake lagate waqt car shake karti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"High speed braking pe zyada hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check brake discs"
],

"repair_cost":{"min":4000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":198,
"problem":"Car Pulls After Service",
"system":"steering",
"component":"alignment",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"pulling after service"
],

"questions":[
{
"id":"q1",
"text":"Service ke baad car pull kar rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Steering alignment theek nahi lag raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"recheck alignment"
],

"repair_cost":{"min":800,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":199,
"problem":"Car Noise After Service",
"system":"general",
"component":"multiple",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"noise after service"
],

"questions":[
{
"id":"q1",
"text":"Service ke baad new noise aayi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Pehle aisa issue nahi tha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"revisit service center"
],

"repair_cost":{"min":0,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":200,
"problem":"Unknown Noise From Engine",
"system":"engine",
"component":"engine system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"unknown engine noise"
],

"questions":[
{
"id":"q1",
"text":"Engine se ajeeb noise aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Noise speed ya RPM se change hoti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"identify noise source"
],

"repair_cost":{"min":1000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},{
"id":201,
"problem":"Car Vibrates While Accelerating",
"system":"drivetrain",
"component":"driveshaft/engine mount",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"vibration during acceleration"
],

"questions":[
{
"id":"q1",
"text":"Acceleration pe vibration feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Speed badhne par vibration badhta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check engine mounts"
],

"repair_cost":{"min":2000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":202,
"problem":"Car Shakes While Idling With AC",
"system":"engine",
"component":"engine mount/AC load",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"vibration with AC on"
],

"questions":[
{
"id":"q1",
"text":"AC ON karte hi vibration badh jata hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"AC OFF karne par smooth ho jata hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe idle with AC"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":203,
"problem":"Car Feels Bumpy On Smooth Road",
"system":"suspension",
"component":"suspension system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"bumpy ride"
],

"questions":[
{
"id":"q1",
"text":"Smooth road pe bhi bumps feel ho rahe hain?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Ride comfort kam ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check shock absorbers"
],

"repair_cost":{"min":3000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":204,
"problem":"Car Feels Floaty At High Speed",
"system":"suspension",
"component":"suspension system",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"unstable high speed"
],

"questions":[
{
"id":"q1",
"text":"High speed pe car floaty feel hoti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Control loose lagta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check suspension and tires"
],

"repair_cost":{"min":3000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":205,
"problem":"Steering Feels Loose At High Speed",
"system":"steering",
"component":"steering system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"loose steering high speed"
],

"questions":[
{
"id":"q1",
"text":"High speed pe steering loose lagta hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Steering control unstable hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check alignment and steering rack"
],

"repair_cost":{"min":3000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":206,
"problem":"Steering Vibrates On Braking",
"system":"steering",
"component":"brake/steering",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"steering vibration braking"
],

"questions":[
{
"id":"q1",
"text":"Brake lagate waqt steering vibrate karta hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"High speed braking pe zyada feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check brake discs"
],

"repair_cost":{"min":4000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":207,
"problem":"Car Drifts On Straight Road",
"system":"steering",
"component":"alignment",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"car drifting"
],

"questions":[
{
"id":"q1",
"text":"Seedhi road pe car drift karti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Steering seedha rakhne par bhi side ja rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check alignment"
],

"repair_cost":{"min":800,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":208,
"problem":"Car Feels Unstable In Crosswind",
"system":"suspension",
"component":"body/suspension",
"severity":"low",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"unstable in wind"
],

"questions":[
{
"id":"q1",
"text":"Crosswind me car unstable lagti hai?",
"impact":{"yes":1.4,"no":0.7}
},
{
"id":"q2",
"text":"High speed pe control mushkil lagta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check tire pressure"
],

"repair_cost":{"min":500,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":209,
"problem":"Gear Hard When Cold",
"system":"transmission",
"component":"gearbox",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"hard gear cold"
],

"questions":[
{
"id":"q1",
"text":"Cold start me gear hard lagta hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Warm hone par smooth ho jata hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe cold vs warm"
],

"repair_cost":{"min":800,"max":4000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":210,
"problem":"Gear Grinding Noise",
"system":"transmission",
"component":"gearbox",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"gear grinding"
],

"questions":[
{
"id":"q1",
"text":"Gear change pe grinding sound aati hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Specific gear me zyada problem hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check clutch and synchronizer"
],

"repair_cost":{"min":8000,"max":30000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":211,
"problem":"Gear Slips Under Load",
"system":"transmission",
"component":"gearbox",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"gear slips under load"
],

"questions":[
{
"id":"q1",
"text":"Load pe gear slip hota hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"RPM badhta hai bina speed ke?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"observe RPM vs speed"
],

"repair_cost":{"min":8000,"max":40000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":212,
"problem":"Clutch Slips Under Load",
"system":"transmission",
"component":"clutch",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"clutch slip under load"
],

"questions":[
{
"id":"q1",
"text":"Load pe clutch slip feel hota hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"RPM badh raha hai bina speed ke?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check clutch plate"
],

"repair_cost":{"min":6000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":213,
"problem":"Clutch Noise When Pressed",
"system":"transmission",
"component":"clutch bearing",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"noise when clutch pressed"
],

"questions":[
{
"id":"q1",
"text":"Clutch dabane pe noise aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Clutch chhodne pe noise band ho jati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe clutch sound"
],

"repair_cost":{"min":5000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":214,
"problem":"Clutch Engages Too Early",
"system":"transmission",
"component":"clutch",
"severity":"low",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"early clutch bite"
],

"questions":[
{
"id":"q1",
"text":"Clutch release karte hi jaldi engage ho jata hai?",
"impact":{"yes":1.4,"no":0.7}
},
{
"id":"q2",
"text":"Driving smooth nahi lagti?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check clutch adjustment"
],

"repair_cost":{"min":1000,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":215,
"problem":"Clutch Engages Too Late",
"system":"transmission",
"component":"clutch",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"late clutch bite"
],

"questions":[
{
"id":"q1",
"text":"Clutch upar chhodne pe engage hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration delayed feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check clutch wear"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":216,
"problem":"Car Overheats After Long Drive",
"system":"cooling",
"component":"cooling system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"overheat after long drive"
],

"questions":[
{
"id":"q1",
"text":"Long drive ke baad overheating hoti hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Short drive me normal hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check coolant flow"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":217,
"problem":"Engine Overheats With Full AC Load",
"system":"cooling",
"component":"cooling system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"overheat AC load"
],

"questions":[
{
"id":"q1",
"text":"Full AC load pe overheating hoti hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"AC off pe normal ho jati hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check radiator fan"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":218,
"problem":"Coolant Overflowing",
"system":"cooling",
"component":"cooling system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"coolant overflow"
],

"questions":[
{
"id":"q1",
"text":"Coolant overflow ho raha hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Engine heat bhi ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check radiator cap"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":219,
"problem":"Coolant Boiling",
"system":"cooling",
"component":"cooling system",
"severity":"critical",
"urgency":"stop_driving",
"probability":4,

"symptoms":[
"coolant boiling"
],

"questions":[
{
"id":"q1",
"text":"Coolant ubal raha hai?",
"impact":{"yes":1.7,"no":0.4}
},
{
"id":"q2",
"text":"Steam nikal rahi hai engine se?",
"impact":{"yes":1.6,"no":0.5}
}
],

"user_checks":[
"stop engine immediately"
],

"repair_cost":{"min":2000,"max":20000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":220,
"problem":"Radiator Fan Always Running",
"system":"cooling",
"component":"fan system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"fan always on"
],

"questions":[
{
"id":"q1",
"text":"Fan continuously chal raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine temperature normal hai phir bhi fan chal raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check temperature sensor"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},{
"id":221,
"problem":"Car Takes Longer To Start",
"system":"engine",
"component":"fuel/ignition",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"delayed start"
],

"questions":[
{
"id":"q1",
"text":"Car start hone me time le rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Multiple self lagani padti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check battery and fuel supply"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":222,
"problem":"Engine Cranks Slow",
"system":"electrical",
"component":"battery/starter",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"slow cranking"
],

"questions":[
{
"id":"q1",
"text":"Engine dheere crank ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Battery weak lag rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check battery voltage"
],

"repair_cost":{"min":2000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":223,
"problem":"Car Shuts Off While Driving",
"system":"engine",
"component":"fuel/electrical",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine shuts off"
],

"questions":[
{
"id":"q1",
"text":"Driving ke beech me car band ho jati hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Restart karne me problem hoti hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check fuel pump"
],

"repair_cost":{"min":3000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":224,
"problem":"Engine Stops At Idle",
"system":"engine",
"component":"idle control",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"engine stops at idle"
],

"questions":[
{
"id":"q1",
"text":"Idle pe engine band ho jata hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration dene par theek ho jata hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe idle behavior"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":225,
"problem":"Car Overheats Randomly",
"system":"cooling",
"component":"cooling system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"random overheating"
],

"questions":[
{
"id":"q1",
"text":"Kabhi-kabhi hi overheating hoti hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Pattern consistent nahi hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"monitor temperature"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":226,
"problem":"Coolant Level Drops Slowly",
"system":"cooling",
"component":"cooling system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"coolant loss"
],

"questions":[
{
"id":"q1",
"text":"Coolant dheere-dheere kam ho raha hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Leak visible nahi hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check hidden leaks"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":227,
"problem":"Engine Temperature Fluctuates",
"system":"cooling",
"component":"temperature system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"temperature fluctuation"
],

"questions":[
{
"id":"q1",
"text":"Temperature up-down ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Gauge stable nahi rehta?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe temperature gauge"
],

"repair_cost":{"min":2000,"max":9000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":228,
"problem":"Fan Not Turning On",
"system":"cooling",
"component":"fan system",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"fan not working"
],

"questions":[
{
"id":"q1",
"text":"Fan bilkul ON nahi ho raha?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Engine heat ho raha hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check fan relay"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":229,
"problem":"Fan Always Running",
"system":"cooling",
"component":"fan system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"fan always on"
],

"questions":[
{
"id":"q1",
"text":"Fan continuously chal raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine normal temperature pe bhi fan ON hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check sensor"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":230,
"problem":"AC Not Cooling At Idle",
"system":"ac",
"component":"ac system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"ac weak at idle"
],

"questions":[
{
"id":"q1",
"text":"Idle pe AC cooling kam ho jati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Drive karte waqt cooling improve hoti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check condenser airflow"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":241,
"problem":"AC Cooling Weak At High Speed",
"system":"ac",
"component":"ac system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"weak AC at high speed"
],

"questions":[
{
"id":"q1",
"text":"High speed pe AC cooling kam ho jati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Idle pe AC theek kaam karta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check refrigerant level"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":242,
"problem":"AC Compressor Not Engaging",
"system":"ac",
"component":"compressor",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"no cooling",
"compressor not engaging"
],

"questions":[
{
"id":"q1",
"text":"AC ON karne par compressor engage nahi hota?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Cooling bilkul nahi aa rahi?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check compressor clutch"
],

"repair_cost":{"min":3000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":243,
"problem":"AC Gas Leak",
"system":"ac",
"component":"ac system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"cooling drops gradually"
],

"questions":[
{
"id":"q1",
"text":"AC cooling dheere-dheere kam ho rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Recent service ke baad issue start hua?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check gas pressure"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":244,
"problem":"Cabin Airflow Weak",
"system":"ac",
"component":"blower/filter",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"low airflow"
],

"questions":[
{
"id":"q1",
"text":"AC airflow kam hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Fan speed badhane par bhi hawa kam aa rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check cabin filter"
],

"repair_cost":{"min":500,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":245,
"problem":"AC Makes Clicking Noise",
"system":"ac",
"component":"compressor/clutch",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"clicking noise"
],

"questions":[
{
"id":"q1",
"text":"AC ON karte hi clicking sound aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Cooling irregular hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check compressor clutch"
],

"repair_cost":{"min":2000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":246,
"problem":"Car Battery Warning Light",
"system":"electrical",
"component":"battery/alternator",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"battery warning light"
],

"questions":[
{
"id":"q1",
"text":"Battery warning light ON hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Car start hone me issue hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check alternator output"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":247,
"problem":"Lights Flickering",
"system":"electrical",
"component":"battery/alternator",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"lights flickering"
],

"questions":[
{
"id":"q1",
"text":"Lights flicker kar rahi hain?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration pe brightness change hoti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check battery and alternator"
],

"repair_cost":{"min":1500,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":248,
"problem":"Horn Not Working",
"system":"electrical",
"component":"horn",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"horn not working"
],

"questions":[
{
"id":"q1",
"text":"Horn bilkul kaam nahi kar raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Fuse check kiya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check horn fuse"
],

"repair_cost":{"min":500,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":249,
"problem":"Wipers Not Working",
"system":"electrical",
"component":"wiper motor",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"wipers not working"
],

"questions":[
{
"id":"q1",
"text":"Wipers kaam nahi kar rahe?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Motor sound bhi nahi aa rahi?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check wiper fuse"
],

"repair_cost":{"min":800,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":250,
"problem":"Dashboard Lights Not Working",
"system":"electrical",
"component":"dashboard system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"dashboard dark"
],

"questions":[
{
"id":"q1",
"text":"Dashboard lights ON nahi ho rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Other electronics kaam kar rahe hain?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check fuse and wiring"
],

"repair_cost":{"min":1000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},
{
"id":261,
"problem":"Central Locking Not Working",
"system":"electrical",
"component":"central locking",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"central locking failure"
],

"questions":[
{
"id":"q1",
"text":"Central locking kaam nahi kar raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Remote se bhi lock/unlock nahi ho raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check key battery"
],

"repair_cost":{"min":500,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":262,
"problem":"Remote Key Not Working",
"system":"electrical",
"component":"key system",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"remote key failure"
],

"questions":[
{
"id":"q1",
"text":"Remote key kaam nahi kar rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Manual key se car open ho rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"replace key battery"
],

"repair_cost":{"min":200,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":263,
"problem":"Car Alarm Triggering Randomly",
"system":"electrical",
"component":"alarm system",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"alarm triggers randomly"
],

"questions":[
{
"id":"q1",
"text":"Alarm bina reason ke baj raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Car locked hone par bhi trigger hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check door sensors"
],

"repair_cost":{"min":500,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":264,
"problem":"Power Windows Slow",
"system":"electrical",
"component":"window motor",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"window slow movement"
],

"questions":[
{
"id":"q1",
"text":"Window dheere move ho rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Sab windows me problem hai ya ek me?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check window channels"
],

"repair_cost":{"min":800,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":265,
"problem":"Seat Adjustment Not Working",
"system":"body",
"component":"seat mechanism",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"seat adjustment failure"
],

"questions":[
{
"id":"q1",
"text":"Seat adjust nahi ho rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Manual ya electric seat hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check seat mechanism"
],

"repair_cost":{"min":1000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":266,
"problem":"Sunroof Not Opening",
"system":"body",
"component":"sunroof system",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"sunroof stuck"
],

"questions":[
{
"id":"q1",
"text":"Sunroof open nahi ho raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Motor sound aa rahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check sunroof track"
],

"repair_cost":{"min":1500,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":267,
"problem":"Water Entering Cabin",
"system":"body",
"component":"seals/drain",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"water leakage inside"
],

"questions":[
{
"id":"q1",
"text":"Car ke andar pani aa raha hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Rain ke baad issue hota hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check door seals"
],

"repair_cost":{"min":1000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":268,
"problem":"Boot Not Opening",
"system":"body",
"component":"boot lock",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"boot stuck"
],

"questions":[
{
"id":"q1",
"text":"Boot open nahi ho raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Remote se bhi open nahi ho raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check latch mechanism"
],

"repair_cost":{"min":800,"max":5000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":269,
"problem":"Fuel Lid Not Opening",
"system":"body",
"component":"fuel lid",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"fuel lid stuck"
],

"questions":[
{
"id":"q1",
"text":"Fuel lid open nahi ho raha?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Manual release try kiya?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check release cable"
],

"repair_cost":{"min":500,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":270,
"problem":"Car Smells Inside",
"system":"general",
"component":"cabin",
"severity":"low",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"bad smell inside"
],

"questions":[
{
"id":"q1",
"text":"Car ke andar smell aa rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"AC ON karte hi smell badh jati hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"clean cabin filter"
],

"repair_cost":{"min":500,"max":3000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":271,
"problem":"Car Smells Burning",
"system":"general",
"component":"engine/brake",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"burning smell"
],

"questions":[
{
"id":"q1",
"text":"Burning smell aa rahi hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Driving ke baad smell aati hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check brakes and wiring"
],

"repair_cost":{"min":1500,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":272,
"problem":"Car Feels Overpowered Suddenly",
"system":"engine",
"component":"throttle system",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"sudden acceleration"
],

"questions":[
{
"id":"q1",
"text":"Car suddenly zyada accelerate karti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Throttle sensitive ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check throttle calibration"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":273,
"problem":"Car Feels Delayed To Respond",
"system":"engine",
"component":"throttle/fuel",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"delayed response"
],

"questions":[
{
"id":"q1",
"text":"Throttle dene par delay feel hota hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration me lag aata hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe throttle response"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":274,
"problem":"Car Feels Smooth But No Power",
"system":"engine",
"component":"engine system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"smooth but weak"
],

"questions":[
{
"id":"q1",
"text":"Car smooth hai lekin power nahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Acceleration weak lag raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check air filter"
],

"repair_cost":{"min":1000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":275,
"problem":"Car Feels Rough But Powerful",
"system":"engine",
"component":"engine system",
"severity":"medium",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"rough but powerful"
],

"questions":[
{
"id":"q1",
"text":"Power hai lekin engine rough lag raha hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Vibration feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check mounts"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":276,
"problem":"Car Stops Suddenly While Braking",
"system":"brake",
"component":"brake system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"sudden stop braking"
],

"questions":[
{
"id":"q1",
"text":"Brake lagate hi car suddenly ruk jati hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Smooth braking nahi ho rahi?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check brake pressure"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":277,
"problem":"Car Takes Longer To Stop",
"system":"brake",
"component":"brake system",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"long braking distance"
],

"questions":[
{
"id":"q1",
"text":"Brake lagane ke baad bhi car jaldi nahi rukti?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Brake weak lag rahe hain?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check brake pads"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":278,
"problem":"Car Rolls On Incline",
"system":"brake",
"component":"brake system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"rolls on slope"
],

"questions":[
{
"id":"q1",
"text":"Slope pe car roll karti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Handbrake hold nahi kar raha?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check handbrake"
],

"repair_cost":{"min":1500,"max":6000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":279,
"problem":"Car Makes Noise Over Bumps",
"system":"suspension",
"component":"suspension system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"noise on bumps"
],

"questions":[
{
"id":"q1",
"text":"Bumps pe awaaz aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Suspension loose lagta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check suspension"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":280,
"problem":"Car Bottom Hits Speed Breaker",
"system":"suspension",
"component":"suspension system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"bottoming out"
],

"questions":[
{
"id":"q1",
"text":"Speed breaker pe car neeche lagti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Ground clearance kam feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check suspension height"
],

"repair_cost":{"min":2000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":281,
"problem":"Car Leans On One Side",
"system":"suspension",
"component":"suspension",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"leaning"
],

"questions":[
{
"id":"q1",
"text":"Car ek side jhuk rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Suspension uneven lagta hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check suspension springs"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":282,
"problem":"Car Makes Noise While Turning",
"system":"steering",
"component":"steering system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"noise while turning"
],

"questions":[
{
"id":"q1",
"text":"Turning pe awaaz aati hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Full turn pe noise zyada hoti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check steering joints"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":283,
"problem":"Steering Feels Heavy At Low Speed",
"system":"steering",
"component":"steering system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"heavy steering low speed"
],

"questions":[
{
"id":"q1",
"text":"Low speed pe steering heavy lagta hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"High speed pe normal ho jata hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check power steering"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":284,
"problem":"Steering Feels Light At High Speed",
"system":"steering",
"component":"steering system",
"severity":"high",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"light steering high speed"
],

"questions":[
{
"id":"q1",
"text":"High speed pe steering bahut light lagta hai?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Control loose lagta hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check steering calibration"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":285,
"problem":"Car Feels Unbalanced",
"system":"general",
"component":"multiple",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"unbalanced feel"
],

"questions":[
{
"id":"q1",
"text":"Car balanced feel nahi ho rahi?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Driving me instability hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check alignment and tires"
],

"repair_cost":{"min":1000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":286,
"problem":"Car Feels Too Sensitive",
"system":"engine",
"component":"throttle",
"severity":"low",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"over sensitive throttle"
],

"questions":[
{
"id":"q1",
"text":"Throttle bahut sensitive ho gaya hai?",
"impact":{"yes":1.4,"no":0.7}
},
{
"id":"q2",
"text":"Light press pe bhi car jump karti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check throttle calibration"
],

"repair_cost":{"min":2000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":287,
"problem":"Car Feels Delayed After Brake Release",
"system":"brake",
"component":"brake system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"delay after braking"
],

"questions":[
{
"id":"q1",
"text":"Brake chhodne ke baad car late move karti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Brake drag feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check brake release"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":288,
"problem":"Car Feels Dragging While Driving",
"system":"brake",
"component":"brake system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"dragging feel"
],

"questions":[
{
"id":"q1",
"text":"Car drag feel ho rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Free roll nahi kar rahi?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check brake calipers"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":289,
"problem":"Car Feels Heavy On One Side",
"system":"suspension",
"component":"suspension",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"heavy one side"
],

"questions":[
{
"id":"q1",
"text":"Car ek side heavy feel ho rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Steering me imbalance feel hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check suspension and brakes"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":290,
"problem":"Car Feels Light On One Side",
"system":"suspension",
"component":"suspension",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"light one side"
],

"questions":[
{
"id":"q1",
"text":"Car ek side light feel ho rahi hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Handling unstable hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check suspension"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":291,
"problem":"Car Feels Jerky In Traffic",
"system":"engine",
"component":"fuel/ignition",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"jerky in traffic"
],

"questions":[
{
"id":"q1",
"text":"Traffic me car jerk karti hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Low speed pe issue zyada hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe low speed behavior"
],

"repair_cost":{"min":2000,"max":12000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":292,
"problem":"Car Feels Smooth On Highway Only",
"system":"engine",
"component":"engine system",
"severity":"low",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"smooth only highway"
],

"questions":[
{
"id":"q1",
"text":"Sirf highway pe smooth feel hoti hai?",
"impact":{"yes":1.4,"no":0.7}
},
{
"id":"q2",
"text":"City me rough lagti hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"compare driving conditions"
],

"repair_cost":{"min":1000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":293,
"problem":"Car Feels Noisy Only On Highway",
"system":"general",
"component":"multiple",
"severity":"low",
"urgency":"service_soon",
"probability":3,

"symptoms":[
"noise highway only"
],

"questions":[
{
"id":"q1",
"text":"Sirf highway pe noise aati hai?",
"impact":{"yes":1.4,"no":0.7}
},
{
"id":"q2",
"text":"High speed pe issue hota hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check tires and wind noise"
],

"repair_cost":{"min":1000,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":294,
"problem":"Car Feels Perfect But Warning Light ON",
"system":"electrical",
"component":"sensor system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"warning light only"
],

"questions":[
{
"id":"q1",
"text":"Car normal chal rahi hai lekin warning light ON hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Performance me koi issue nahi hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"scan OBD codes"
],

"repair_cost":{"min":1000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":295,
"problem":"Car Suddenly Feels Different",
"system":"general",
"component":"multiple",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"changed behavior"
],

"questions":[
{
"id":"q1",
"text":"Car ka behavior suddenly change ho gaya?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Driving feel different lag raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"observe changes"
],

"repair_cost":{"min":1000,"max":15000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":296,
"problem":"Car Feels Perfect But Fuel High",
"system":"engine",
"component":"fuel system",
"severity":"medium",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"high fuel consumption"
],

"questions":[
{
"id":"q1",
"text":"Mileage kam ho gaya hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Driving same hone ke baad bhi fuel zyada lag raha hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check tire pressure"
],

"repair_cost":{"min":500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":297,
"problem":"Car Feels Perfect But AC Weak",
"system":"ac",
"component":"ac system",
"severity":"low",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"ac weak only"
],

"questions":[
{
"id":"q1",
"text":"Sirf AC cooling weak hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Engine performance normal hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check AC gas"
],

"repair_cost":{"min":1500,"max":8000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":298,
"problem":"Car Feels Perfect But Brake Weak",
"system":"brake",
"component":"brake system",
"severity":"high",
"urgency":"service_soon",
"probability":5,

"symptoms":[
"brake weak only"
],

"questions":[
{
"id":"q1",
"text":"Sirf brake weak lag rahe hain?",
"impact":{"yes":1.6,"no":0.5}
},
{
"id":"q2",
"text":"Stopping distance badh gaya hai?",
"impact":{"yes":1.5,"no":0.6}
}
],

"user_checks":[
"check brake pads"
],

"repair_cost":{"min":2000,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":299,
"problem":"Car Feels Perfect But Steering Issue",
"system":"steering",
"component":"steering system",
"severity":"medium",
"urgency":"service_soon",
"probability":4,

"symptoms":[
"steering only issue"
],

"questions":[
{
"id":"q1",
"text":"Sirf steering me problem hai?",
"impact":{"yes":1.5,"no":0.6}
},
{
"id":"q2",
"text":"Baaki car normal hai?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"check steering alignment"
],

"repair_cost":{"min":1500,"max":10000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
},

{
"id":300,
"problem":"No Problem But User Wants Check",
"system":"general",
"component":"general",
"severity":"low",
"urgency":"normal",
"probability":3,

"symptoms":[
"no issue"
],

"questions":[
{
"id":"q1",
"text":"Koi specific problem nahi hai?",
"impact":{"yes":1.4,"no":0.7}
},
{
"id":"q2",
"text":"General check karwana chahte ho?",
"impact":{"yes":1.4,"no":0.7}
}
],

"user_checks":[
"general inspection"
],

"repair_cost":{"min":500,"max":2000},

"learning":{"success_count":0,"fail_count":0},
"feedback":{"confirmed":0,"rejected":0}
}]

ALLOWED_URGENCY_VALUES = {"normal", "service_soon", "repair_immediately", "stop_driving"}
ALLOWED_SEVERITY_VALUES = {"low", "medium", "high", "critical"}

DIAGNOSIS_DISCLAIMER = (
    "AMPYAN provides informational guidance only. Confirm the issue with a qualified mechanic "
    "before making repair or safety decisions."
)

STOP_DRIVING_MESSAGE = (
    "Do not drive the vehicle. Stop safely and contact a qualified mechanic or roadside assistance."
)

REPAIR_IMMEDIATELY_MESSAGE = (
    "This may affect safety or reliability. Get the vehicle inspected as soon as possible."
)


def _slug(value):
    return "".join(ch if ch.isalnum() else "_" for ch in (value or "").lower()).strip("_")


KNOWN_DIAGNOSIS_GROUPS = {
    "ignition_coil_failure": {
        "problems": {"Ignition Coil Failure"},
        "aliases": ["coil pack failure", "ignition coil weak", "engine misfire due to coil"],
    },
    "fuel_injector_clogged": {
        "problems": {"Fuel Injector Clogged"},
        "aliases": ["dirty fuel injector", "injector blockage", "fuel injector restriction"],
    },
    "engine_mount_worn": {
        "problems": {"Engine Mount Worn"},
        "aliases": ["engine mounting worn", "mount vibration", "engine support wear"],
    },
    "oxygen_sensor_fault": {
        "problems": {"Oxygen Sensor Fault"},
        "aliases": ["o2 sensor fault", "lambda sensor issue", "oxygen sensor failure"],
    },
    "horn_not_working": {
        "problems": {"Horn Not Working"},
        "aliases": ["horn failure", "horn fuse issue", "horn circuit fault"],
    },
    "brake_disc_vibration": {
        "problems": {"Brake Disc Warped", "Brake Pedal Vibrates", "Car Shakes While Braking"},
        "aliases": ["warped brake disc", "brake judder", "brake vibration"],
    },
    "cooling_fan_overheat": {
        "problems": {"Radiator Fan Failure", "Fan Not Turning On", "Car Overheats In Traffic Only"},
        "aliases": ["cooling fan not working", "radiator fan issue", "traffic overheating"],
    },
    "head_gasket_smoke_coolant": {
        "problems": {"Engine Head Gasket Leak", "White Smoke From Exhaust", "Coolant Mixed With Oil"},
        "aliases": ["white smoke coolant loss", "head gasket failure", "coolant entering cylinder"],
    },
    "brake_hydraulic_failure": {
        "problems": {"Brake Pedal Goes To Floor", "Brake Fluid Low", "Brake Weak"},
        "aliases": ["brake pedal sinking", "brake pressure loss", "hydraulic brake failure"],
    },
}

STOP_DRIVING_PROBLEMS = {
    "Brake Pedal Goes To Floor",
    "Check Engine Light Flashing",
    "Coolant Boiling",
    "Engine Seized",
    "Engine Head Gasket Leak",
    "White Smoke From Exhaust",
    "Coolant Mixed With Oil",
    "Timing Belt Worn",
    "Car Not Moving In Gear",
}

REPAIR_IMMEDIATELY_PROBLEMS = {
    "Fuel Smell Inside Cabin",
    "Fuel Injector Leak",
    "Electric Power Steering Failure",
    "Fan Not Turning On",
    "Radiator Fan Failure",
    "Cooling Fan Relay Failure",
    "Car Overheats In Traffic Only",
    "Brake Pedal Goes To Floor",
    "Car Takes Longer To Stop",
    "Car Feels Perfect But Brake Weak",
    "Brake Pedal Goes To Floor",
    "Brake Fluid Low",
    "Brake Caliper Stuck",
    "Car Shuts Off While Driving",
    "Fuel Smell Inside Cabin",
}

GENERIC_ROUTER_PROBLEM_TOKENS = (
    "unknown",
    "general",
    "multiple",
    "feels perfect but",
    "feels heavy",
    "feels different",
    "feels unbalanced",
    "feels smooth",
    "feels rough",
    "no problem",
)


def _default_safety_message(urgency):
    if urgency == "stop_driving":
        return STOP_DRIVING_MESSAGE
    if urgency == "repair_immediately":
        return REPAIR_IMMEDIATELY_MESSAGE
    return ""


def _ensure_question_impact(entry):
    for question in entry.get("questions", []):
        question.setdefault("impact", {"yes": 1.5, "no": 0.6})


def _apply_grouping(entry):
    problem = entry.get("problem")
    for group_id, config in KNOWN_DIAGNOSIS_GROUPS.items():
        if problem in config["problems"]:
            entry["group_id"] = group_id
            existing_aliases = entry.get("aliases", [])
            entry["aliases"] = sorted(set(existing_aliases + config["aliases"]))
            return

    entry.setdefault("group_id", _slug(problem))


def _is_generic_router(entry):
    problem = (entry.get("problem") or "").lower()
    system = (entry.get("system") or "").lower()
    component = (entry.get("component") or "").lower()
    return (
        any(token in problem for token in GENERIC_ROUTER_PROBLEM_TOKENS)
        or system == "general"
        or component in {"general", "multiple"}
    )


def harden_failure_database_entries(entries):
    seen_problem_counts = {}

    for entry in entries:
        problem = entry.get("problem", "")

        _ensure_question_impact(entry)
        _apply_grouping(entry)

        seen_problem_counts[problem] = seen_problem_counts.get(problem, 0) + 1
        if seen_problem_counts[problem] > 1:
            entry["is_duplicate_alias"] = True
            entry.setdefault("canonical_problem", problem)

        if problem in STOP_DRIVING_PROBLEMS:
            entry["urgency"] = "stop_driving"
            entry["severity"] = "critical"
        elif problem in REPAIR_IMMEDIATELY_PROBLEMS:
            entry["urgency"] = "repair_immediately"
            if entry.get("severity") == "low":
                entry["severity"] = "medium"

        if entry.get("urgency") == "urgent":
            entry["urgency"] = "repair_immediately"
        elif entry.get("urgency") == "immediate":
            entry["urgency"] = "repair_immediately"

        if _is_generic_router(entry):
            entry["is_generic"] = True
            entry["use_as_router_only"] = True
        else:
            entry.setdefault("is_generic", False)
            entry.setdefault("use_as_router_only", False)

        entry.setdefault("safety_message", _default_safety_message(entry.get("urgency")))
        if not entry["safety_message"]:
            entry["safety_message"] = _default_safety_message(entry.get("urgency"))
        entry.setdefault("disclaimer", DIAGNOSIS_DISCLAIMER)

    return entries


def validate_failure_database(entries=None):
    entries = entries or FAILURE_DATABASE
    report = {
        "total_entries": len(entries),
        "duplicate_problem_names": {},
        "duplicate_symptom_overlap": [],
        "missing_required_fields": [],
        "missing_question_impact": [],
        "invalid_urgency": [],
        "invalid_severity": [],
        "invalid_repair_cost": [],
        "empty_symptoms": [],
        "empty_questions": [],
        "missing_id_ranges": [],
    }

    required_fields = {
        "id", "problem", "system", "component", "severity", "urgency", "probability",
        "symptoms", "questions", "user_checks", "repair_cost",
    }
    problem_map = {}
    symptom_map = {}
    ids = set()

    for entry in entries:
        entry_id = entry.get("id")
        ids.add(entry_id)

        missing = sorted(required_fields - set(entry.keys()))
        if missing:
            report["missing_required_fields"].append({"id": entry_id, "missing": missing})

        problem = entry.get("problem", "")
        problem_map.setdefault(problem.lower(), []).append(entry_id)

        symptoms = entry.get("symptoms", [])
        questions = entry.get("questions", [])
        if not symptoms:
            report["empty_symptoms"].append(entry_id)
        if not questions:
            report["empty_questions"].append(entry_id)

        for question in questions:
            impact = question.get("impact")
            if not isinstance(impact, dict) or "yes" not in impact or "no" not in impact:
                report["missing_question_impact"].append({"id": entry_id, "question_id": question.get("id")})

        urgency = entry.get("urgency")
        severity = entry.get("severity")
        if urgency not in ALLOWED_URGENCY_VALUES:
            report["invalid_urgency"].append({"id": entry_id, "urgency": urgency})
        if severity not in ALLOWED_SEVERITY_VALUES:
            report["invalid_severity"].append({"id": entry_id, "severity": severity})

        repair_cost = entry.get("repair_cost", {})
        if isinstance(repair_cost, dict) and repair_cost.get("min", 0) > repair_cost.get("max", 0):
            report["invalid_repair_cost"].append({"id": entry_id, "repair_cost": repair_cost})

        for symptom in symptoms:
            symptom_map.setdefault(symptom, []).append(entry_id)

    report["duplicate_problem_names"] = {
        problem: entry_ids
        for problem, entry_ids in problem_map.items()
        if len(entry_ids) > 1
    }
    report["duplicate_symptom_overlap"] = [
        {"symptom": symptom, "ids": entry_ids}
        for symptom, entry_ids in symptom_map.items()
        if len(entry_ids) > 8
    ]

    if ids:
        for missing_id in range(min(ids), max(ids) + 1):
            if missing_id not in ids:
                report["missing_id_ranges"].append(missing_id)

    return report


FAILURE_DATABASE = harden_failure_database_entries(
    normalize_failure_database_entries(FAILURE_DATABASE)
)
