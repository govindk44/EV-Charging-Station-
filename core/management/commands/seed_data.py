import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User, Vehicle
from charging.models import Booking, ChargingSession
from stations.models import Charger, Station

BANGALORE_STATIONS = [
    {"name": "Tata Power - Koramangala", "address": "80 Feet Road, Koramangala 4th Block", "city": "Bangalore", "state": "Karnataka", "pincode": "560034", "lat": 12.9352, "lng": 77.6245},
    {"name": "EESL ChargePoint - Whitefield", "address": "ITPL Main Road, Whitefield", "city": "Bangalore", "state": "Karnataka", "pincode": "560066", "lat": 12.9698, "lng": 77.7500},
    {"name": "Ather Grid - Indiranagar", "address": "100 Feet Road, Indiranagar", "city": "Bangalore", "state": "Karnataka", "pincode": "560038", "lat": 12.9784, "lng": 77.6408},
    {"name": "Fortum Charge - MG Road", "address": "MG Road, Near Trinity Circle", "city": "Bangalore", "state": "Karnataka", "pincode": "560001", "lat": 12.9756, "lng": 77.6068},
    {"name": "Tata Power - Electronic City", "address": "Phase 1, Electronic City", "city": "Bangalore", "state": "Karnataka", "pincode": "560100", "lat": 12.8440, "lng": 77.6732},
    {"name": "ChargeZone - HSR Layout", "address": "27th Main Road, HSR Layout Sector 1", "city": "Bangalore", "state": "Karnataka", "pincode": "560102", "lat": 12.9116, "lng": 77.6389},
    {"name": "Ather Grid - Jayanagar", "address": "11th Main Road, 4th Block Jayanagar", "city": "Bangalore", "state": "Karnataka", "pincode": "560011", "lat": 12.9308, "lng": 77.5838},
    {"name": "Statiq - Marathahalli", "address": "Outer Ring Road, Marathahalli Bridge", "city": "Bangalore", "state": "Karnataka", "pincode": "560037", "lat": 12.9591, "lng": 77.7007},
    {"name": "Tata Power - Yelahanka", "address": "Bellary Road, Near Yelahanka Junction", "city": "Bangalore", "state": "Karnataka", "pincode": "560064", "lat": 13.1007, "lng": 77.5963},
    {"name": "EESL - Bannerghatta Road", "address": "Bannerghatta Main Road, Arekere", "city": "Bangalore", "state": "Karnataka", "pincode": "560076", "lat": 12.8882, "lng": 77.5972},
    {"name": "ChargeZone - BTM Layout", "address": "16th Main Road, BTM 2nd Stage", "city": "Bangalore", "state": "Karnataka", "pincode": "560076", "lat": 12.9166, "lng": 77.6101},
    {"name": "Fortum Charge - JP Nagar", "address": "15th Cross, JP Nagar Phase 6", "city": "Bangalore", "state": "Karnataka", "pincode": "560078", "lat": 12.9063, "lng": 77.5857},
    {"name": "Ather Grid - Hebbal", "address": "Bellary Road, Near Hebbal Flyover", "city": "Bangalore", "state": "Karnataka", "pincode": "560024", "lat": 13.0358, "lng": 77.5970},
    {"name": "Statiq - KR Puram", "address": "Old Madras Road, Near KR Puram Station", "city": "Bangalore", "state": "Karnataka", "pincode": "560036", "lat": 13.0012, "lng": 77.6966},
    {"name": "Tata Power - Sarjapur Road", "address": "Sarjapur Main Road, Near Wipro Junction", "city": "Bangalore", "state": "Karnataka", "pincode": "560035", "lat": 12.9107, "lng": 77.6872},
    {"name": "ChargeZone - Bellandur", "address": "Outer Ring Road, Near Bellandur Gate", "city": "Bangalore", "state": "Karnataka", "pincode": "560103", "lat": 12.9252, "lng": 77.6742},
    {"name": "EESL - Domlur", "address": "Intermediate Ring Road, Domlur", "city": "Bangalore", "state": "Karnataka", "pincode": "560071", "lat": 12.9607, "lng": 77.6387},
    {"name": "Fortum Charge - Richmond Road", "address": "Richmond Road, Near Richmond Circle", "city": "Bangalore", "state": "Karnataka", "pincode": "560025", "lat": 12.9658, "lng": 77.5981},
    {"name": "Ather Grid - Malleshwaram", "address": "Sampige Road, Malleshwaram", "city": "Bangalore", "state": "Karnataka", "pincode": "560003", "lat": 12.9990, "lng": 77.5700},
    {"name": "Statiq - Rajajinagar", "address": "Dr Rajkumar Road, Rajajinagar 1st Block", "city": "Bangalore", "state": "Karnataka", "pincode": "560010", "lat": 12.9893, "lng": 77.5554},
    {"name": "Tata Power - Koramangala 6th Block", "address": "80 Feet Road, 6th Block Koramangala", "city": "Bangalore", "state": "Karnataka", "pincode": "560095", "lat": 12.9340, "lng": 77.6190},
    {"name": "ChargeZone - Whitefield Main", "address": "Whitefield Main Road, Near Forum Shantiniketan", "city": "Bangalore", "state": "Karnataka", "pincode": "560066", "lat": 12.9770, "lng": 77.7250},
]

CHARGER_CONFIGS = [
    {"type": "Type2", "power": 7.4, "price": 12.00, "connector": "Type2"},
    {"type": "Type2", "power": 22.0, "price": 15.00, "connector": "Type2"},
    {"type": "CCS", "power": 50.0, "price": 18.00, "connector": "CCS2"},
    {"type": "DC-Fast", "power": 120.0, "price": 22.00, "connector": "CCS2"},
    {"type": "CHAdeMO", "power": 50.0, "price": 17.00, "connector": "CHAdeMO"},
    {"type": "DC-Fast", "power": 150.0, "price": 25.00, "connector": "CCS2"},
]

TEST_USERS = [
    {"email": "rahul.sharma@test.com", "username": "rahul_sharma", "first_name": "Rahul", "last_name": "Sharma", "phone": "9876543210"},
    {"email": "priya.patel@test.com", "username": "priya_patel", "first_name": "Priya", "last_name": "Patel", "phone": "9876543211"},
    {"email": "amit.kumar@test.com", "username": "amit_kumar", "first_name": "Amit", "last_name": "Kumar", "phone": "9876543212"},
    {"email": "sneha.reddy@test.com", "username": "sneha_reddy", "first_name": "Sneha", "last_name": "Reddy", "phone": "9876543213"},
    {"email": "vikram.singh@test.com", "username": "vikram_singh", "first_name": "Vikram", "last_name": "Singh", "phone": "9876543214"},
    {"email": "ananya.das@test.com", "username": "ananya_das", "first_name": "Ananya", "last_name": "Das", "phone": "9876543215"},
    {"email": "karthik.nair@test.com", "username": "karthik_nair", "first_name": "Karthik", "last_name": "Nair", "phone": "9876543216"},
    {"email": "meera.iyer@test.com", "username": "meera_iyer", "first_name": "Meera", "last_name": "Iyer", "phone": "9876543217"},
    {"email": "arjun.menon@test.com", "username": "arjun_menon", "first_name": "Arjun", "last_name": "Menon", "phone": "9876543218"},
    {"email": "divya.gupta@test.com", "username": "divya_gupta", "first_name": "Divya", "last_name": "Gupta", "phone": "9876543219"},
]

TEST_VEHICLES = [
    {"make": "Tata", "model": "Nexon EV Max", "year": 2024, "battery": 40.5, "connector": "CCS", "plate": "KA01AB1234"},
    {"make": "MG", "model": "ZS EV", "year": 2024, "battery": 50.3, "connector": "CCS", "plate": "KA01CD5678"},
    {"make": "Hyundai", "model": "Kona Electric", "year": 2023, "battery": 39.2, "connector": "CCS", "plate": "KA02EF9012"},
    {"make": "Tata", "model": "Tiago EV", "year": 2024, "battery": 24.0, "connector": "CCS", "plate": "KA03GH3456"},
    {"make": "BYD", "model": "Atto 3", "year": 2024, "battery": 60.5, "connector": "CCS", "plate": "KA04IJ7890"},
    {"make": "Mahindra", "model": "XUV400", "year": 2024, "battery": 39.4, "connector": "CCS", "plate": "KA05KL1122"},
    {"make": "Kia", "model": "EV6", "year": 2024, "battery": 77.4, "connector": "CCS", "plate": "KA01MN3344"},
    {"make": "BMW", "model": "iX1", "year": 2024, "battery": 66.5, "connector": "CCS", "plate": "KA01OP5566"},
    {"make": "Mercedes", "model": "EQB", "year": 2023, "battery": 66.5, "connector": "CCS", "plate": "KA02QR7788"},
    {"make": "Tata", "model": "Punch EV", "year": 2025, "battery": 35.0, "connector": "CCS", "plate": "KA03ST9900"},
]

AMENITIES_POOL = [
    ["WiFi", "Restroom", "Cafe"],
    ["WiFi", "Restroom", "Parking"],
    ["WiFi", "Restroom", "Cafe", "Shopping"],
    ["Restroom", "Parking"],
    ["WiFi", "Restroom"],
    ["WiFi", "Restroom", "Cafe", "Lounge"],
    ["Restroom", "Parking", "Security"],
]


class Command(BaseCommand):
    help = "Seed the database with realistic EV charging data for Bangalore"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            ChargingSession.objects.all().delete()
            Booking.objects.all().delete()
            Charger.objects.all().delete()
            Station.objects.all().delete()
            Vehicle.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        self._create_admin()
        station_owners = self._create_station_owners()
        users = self._create_users()
        vehicles = self._create_vehicles(users)
        stations = self._create_stations(station_owners)
        chargers = self._create_chargers(stations)
        self._create_sessions(users, vehicles, chargers)

        self.stdout.write(self.style.SUCCESS("\nSeeding completed successfully!"))
        self.stdout.write(f"  Admin: admin@evcharge.com / admin123456")
        self.stdout.write(f"  Station Owners: owner1@evcharge.com, owner2@evcharge.com / owner123456")
        self.stdout.write(f"  Test Users: {TEST_USERS[0]['email']} / test123456")
        self.stdout.write(f"  Stations: {Station.objects.count()}")
        self.stdout.write(f"  Chargers: {Charger.objects.count()}")
        self.stdout.write(f"  Users: {User.objects.count()}")
        self.stdout.write(f"  Vehicles: {Vehicle.objects.count()}")
        self.stdout.write(f"  Bookings: {Booking.objects.count()}")
        self.stdout.write(f"  Sessions: {ChargingSession.objects.count()}")

    def _create_admin(self):
        admin, created = User.objects.get_or_create(
            email="admin@evcharge.com",
            defaults={
                "username": "admin",
                "first_name": "System",
                "last_name": "Admin",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin123456")
            admin.save()
            self.stdout.write(f"  Created admin user: {admin.email}")
        return admin

    def _create_station_owners(self):
        owners = []
        for i in range(1, 4):
            owner, created = User.objects.get_or_create(
                email=f"owner{i}@evcharge.com",
                defaults={
                    "username": f"station_owner_{i}",
                    "first_name": f"Owner{i}",
                    "last_name": "Manager",
                    "role": "station_owner",
                    "phone": f"98765000{i}0",
                },
            )
            if created:
                owner.set_password("owner123456")
                owner.save()
                self.stdout.write(f"  Created station owner: {owner.email}")
            owners.append(owner)
        return owners

    def _create_users(self):
        users = []
        for u in TEST_USERS:
            user, created = User.objects.get_or_create(
                email=u["email"],
                defaults={
                    "username": u["username"],
                    "first_name": u["first_name"],
                    "last_name": u["last_name"],
                    "phone": u["phone"],
                    "role": "user",
                },
            )
            if created:
                user.set_password("test123456")
                user.save()
            users.append(user)
        self.stdout.write(f"  Created {len(users)} test users")
        return users

    def _create_vehicles(self, users):
        vehicles = []
        for i, v in enumerate(TEST_VEHICLES):
            vehicle, created = Vehicle.objects.get_or_create(
                license_plate=v["plate"],
                defaults={
                    "user": users[i % len(users)],
                    "make": v["make"],
                    "model_name": v["model"],
                    "year": v["year"],
                    "battery_capacity_kwh": Decimal(str(v["battery"])),
                    "connector_type": v["connector"],
                },
            )
            vehicles.append(vehicle)
        self.stdout.write(f"  Created {len(vehicles)} vehicles")
        return vehicles

    def _create_stations(self, owners):
        stations = []
        for i, s in enumerate(BANGALORE_STATIONS):
            station, created = Station.objects.get_or_create(
                name=s["name"],
                defaults={
                    "address": s["address"],
                    "city": s["city"],
                    "state": s["state"],
                    "pincode": s["pincode"],
                    "latitude": Decimal(str(s["lat"])),
                    "longitude": Decimal(str(s["lng"])),
                    "owner": owners[i % len(owners)],
                    "is_active": True,
                    "opening_time": "06:00:00",
                    "closing_time": "23:00:00",
                    "amenities": random.choice(AMENITIES_POOL),
                    "contact_number": f"080-{random.randint(40000000, 49999999)}",
                },
            )
            stations.append(station)
        self.stdout.write(f"  Created {len(stations)} stations")
        return stations

    def _create_chargers(self, stations):
        chargers = []
        serial_counter = 1
        for station in stations:
            num_chargers = random.randint(2, 5)
            selected_configs = random.sample(
                CHARGER_CONFIGS, min(num_chargers, len(CHARGER_CONFIGS))
            )
            for cfg in selected_configs:
                status_val = random.choices(
                    ["available", "busy", "maintenance", "offline"],
                    weights=[60, 25, 10, 5],
                    k=1,
                )[0]
                charger, created = Charger.objects.get_or_create(
                    serial_number=f"EVC-BLR-{serial_counter:04d}",
                    defaults={
                        "station": station,
                        "charger_type": cfg["type"],
                        "power_kw": Decimal(str(cfg["power"])),
                        "connector_type": cfg["connector"],
                        "base_price_per_kwh": Decimal(str(cfg["price"])),
                        "status": status_val,
                    },
                )
                chargers.append(charger)
                serial_counter += 1
        self.stdout.write(f"  Created {len(chargers)} chargers")
        return chargers

    def _create_sessions(self, users, vehicles, chargers):
        now = timezone.now()
        available_chargers = [c for c in chargers if c.status == "available"]
        busy_chargers = [c for c in chargers if c.status == "busy"]

        booking_count = 0
        session_count = 0

        for i in range(15):
            user = random.choice(users)
            charger = random.choice(available_chargers) if available_chargers else random.choice(chargers)
            vehicle = random.choice([v for v in vehicles if v.user == user] or vehicles)

            days_ago = random.randint(1, 14)
            start = now - timedelta(days=days_ago, hours=random.randint(0, 12))
            duration_hours = round(random.uniform(0.5, 3.0), 1)
            end = start + timedelta(hours=duration_hours)

            booking = Booking.objects.create(
                user=user,
                charger=charger,
                vehicle=vehicle,
                scheduled_start=start,
                scheduled_end=end,
                status="completed",
            )
            booking_count += 1

            energy = Decimal(str(round(
                float(charger.power_kw) * duration_hours * random.uniform(0.6, 0.95), 3
            )))
            hour = start.hour
            from core.utils import get_pricing_label, get_pricing_multiplier
            multiplier = get_pricing_multiplier(hour)
            tier = get_pricing_label(hour)
            effective_rate = charger.base_price_per_kwh * multiplier
            energy_cost = (energy * effective_rate).quantize(Decimal("0.01"))

            overstay_min = random.choices([0, 0, 0, 5, 12, 25], weights=[40, 20, 15, 10, 10, 5], k=1)[0]
            overstay_fine = Decimal(str(overstay_min * 5))
            actual_end = end + timedelta(minutes=overstay_min) if overstay_min else end

            ChargingSession.objects.create(
                booking=booking,
                user=user,
                charger=charger,
                vehicle=vehicle,
                start_time=start,
                end_time=actual_end,
                energy_consumed_kwh=energy,
                base_rate_per_kwh=charger.base_price_per_kwh,
                peak_multiplier=multiplier,
                pricing_tier=tier,
                energy_cost=energy_cost,
                overstay_minutes=overstay_min,
                overstay_fine=overstay_fine,
                total_cost=energy_cost + overstay_fine,
                status="completed",
            )
            session_count += 1

        for charger in busy_chargers[:3]:
            user = random.choice(users)
            vehicle = random.choice([v for v in vehicles if v.user == user] or vehicles)
            start = now - timedelta(minutes=random.randint(10, 90))

            booking = Booking.objects.create(
                user=user,
                charger=charger,
                vehicle=vehicle,
                scheduled_start=start,
                scheduled_end=start + timedelta(hours=2),
                status="active",
            )
            booking_count += 1

            multiplier = get_pricing_multiplier(start.hour)
            tier = get_pricing_label(start.hour)

            ChargingSession.objects.create(
                booking=booking,
                user=user,
                charger=charger,
                vehicle=vehicle,
                start_time=start,
                base_rate_per_kwh=charger.base_price_per_kwh,
                peak_multiplier=multiplier,
                pricing_tier=tier,
                status="active",
            )
            session_count += 1

        for i in range(5):
            user = random.choice(users)
            charger = random.choice(available_chargers) if available_chargers else random.choice(chargers)
            vehicle = random.choice([v for v in vehicles if v.user == user] or vehicles)
            start = now + timedelta(hours=random.randint(2, 48))
            end = start + timedelta(hours=random.uniform(1, 3))

            Booking.objects.create(
                user=user,
                charger=charger,
                vehicle=vehicle,
                scheduled_start=start,
                scheduled_end=end,
                status="confirmed",
            )
            booking_count += 1

        self.stdout.write(f"  Created {booking_count} bookings and {session_count} sessions")
