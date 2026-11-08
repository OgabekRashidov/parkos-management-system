from django.test import TestCase
from parking.models import Vehicle, VehicleType
from parking.services.parking_service import ParkingService


class ParkingServiceTest(TestCase):
    def setUp(self):
        self.kind = VehicleType.objects.create(
            name="Yengil avtomobil",
            price=5000
        )

    def test_register_vehicle(self):
        vehicle = ParkingService.register_vehicle(
            "01A123AA", self.kind
        )
        self.assertEqual(vehicle.plate, "01A123AA")
        self.assertEqual(Vehicle.objects.count(), 1)

    def test_duplicate_plate_is_rejected(self):
        ParkingService.register_vehicle("01A123AA", self.kind)
        with self.assertRaises(ValueError):
            ParkingService.register_vehicle("01A123AA", self.kind)
