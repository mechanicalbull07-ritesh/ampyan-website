import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ai_engine.diagnostic_engine import diagnose_vehicle


CASES = [
    ("brake pedal goes to floor", {"Brake Pedal Goes To Floor"}),
    ("car vibrates when braking at high speed", {"Brake Disc Warped", "Brake Pedal Vibrates", "Car Shakes While Braking"}),
    ("engine overheating fan not working", {"Radiator Fan Failure", "Cooling Fan Relay Failure", "Fan Not Turning On"}),
    ("car not starting only clicking sound", {"Battery Dead", "Loose Battery Terminal", "Starter Motor Failure"}),
    ("ac not cooling but blower working", {"AC Gas Low", "AC Gas Leak", "AC Compressor Failure"}),
    ("steering pulls to left while driving", {"Wheel Alignment Incorrect"}),
    ("engine misfire rough idle petrol smell", {"Spark Plug Fouled", "Spark Plug Worn", "Ignition Coil Failure"}),
    ("white smoke from exhaust and coolant level low", {"White Smoke From Exhaust", "Engine Head Gasket Leak"}),
    ("brake lagane par steering vibrate hoti hai", {"Brake Disc Warped", "Brake Pedal Vibrates", "Car Shakes While Braking"}),
    ("radiator fan nahi chal raha aur engine garam ho raha hai", {"Radiator Fan Failure", "Cooling Fan Relay Failure", "Fan Not Turning On"}),
    ("gadi seedhi road pe ek side khich rahi hai", {"Wheel Alignment Incorrect"}),
    ("ac blower chal raha par thandi hawa nahi aa rahi", {"AC Gas Low", "AC Gas Leak", "AC Compressor Failure"}),
    ("silencer se safed dhuan aa raha coolant kam hai", {"White Smoke From Exhaust", "Engine Head Gasket Leak"}),
    ("gear change hard hai clutch se burning smell aa rahi hai", {"Clutch Plate Worn", "Clutch Slips Under Load", "Clutch Pedal Hard"}),
    ("speed badhne par humming noise aa rahi hai", {"Wheel Bearing Failure"}),
    ("tail light ignition off ke baad bhi on rehti hai", {"Tail Light Stays On After Ignition Off"}),
    ("headlight throw low hai raat me visibility kam hai", {"Headlight Low Beam Weak"}),
    ("check engine light on hai", {"Check Engine Light Solid"}),
    ("check engine light blink kar rahi hai", {"Check Engine Light Flashing"}),
    ("oil pressure red oil light on dashboard", {"Oil Pressure Warning Light On"}),
    ("temperature warning light on hai engine garam", {"Temperature Warning Light On"}),
    ("parking brake release ke baad bhi brake warning light on hai", {"Brake Warning Light On"}),
    ("tpms tyre pressure light on hai", {"TPMS Warning Light On"}),
    ("dashboard light photo uploaded unknown symbol", {"Dashboard Warning Light Photo Review Needed"}),
    ("basic maintenance checklist batao", {"Basic Maintenance Schedule Guidance"}),
    ("engine oil kab change karna chahiye", {"Engine Oil Change Guidance"}),
    ("tyre pressure kitna check karna hai aur rotation kab", {"Tyre Pressure And Rotation Guidance"}),
    ("battery health check kab karwana chahiye", {"Battery Maintenance Guidance"}),
    ("brake pad kab change karna chahiye", {"Brake Maintenance Guidance"}),
    ("coolant kab change karna chahiye", {"Coolant Maintenance Guidance"}),
    ("air filter cabin filter kab change hota hai", {"Filter Maintenance Guidance"}),
    ("long trip se pehle maintenance checklist", {"Long Trip Maintenance Checklist"}),
    ("brake squeaking noise while braking", {"Brake Pad Wear"}),
    ("car pulls to one side while braking", {"Brake Caliper Stuck"}),
    ("black smoke from exhaust acceleration", {"Black Smoke From Exhaust"}),
    ("blue smoke from exhaust oil burning", {"Blue Smoke From Exhaust", "Turbocharger Oil Leak"}),
    ("clutch slipping rpm increases speed not increasing", {"Clutch Slips Under Load"}),
    ("car shuts off while driving", {"Car Shuts Off While Driving"}),
    ("abs light on dashboard", {"ABS Sensor Fault", "ABS Module Failure"}),
    ("airbag light on dashboard", {"Airbag Warning Light"}),
]


def main():
    failures = []
    for symptom, expected in CASES:
        results, _ = diagnose_vehicle(symptom)
        top = results[0]["issue"] if results else None
        confidence = results[0].get("confidence") if results else None
        calibrated = confidence is not None and 25 <= confidence <= 95
        ok = top in expected and calibrated
        print(f"{'PASS' if ok else 'FAIL'} | {symptom} -> {top} ({confidence})")
        if not ok:
            failures.append((symptom, top, sorted(expected)))

    vague_results, _ = diagnose_vehicle("car problem")
    vague_confidence = vague_results[0].get("confidence") if vague_results else 0
    vague_ok = vague_confidence < 75
    print(f"{'PASS' if vague_ok else 'FAIL'} | vague confidence calibrated -> {vague_confidence}")
    if not vague_ok:
        failures.append(("car problem", vague_results[0].get("issue") if vague_results else None, ["confidence below 75"]))

    if failures:
        print("\nFailures:")
        for symptom, top, expected in failures:
            print(f"- {symptom}: got {top}, expected one of {expected}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
