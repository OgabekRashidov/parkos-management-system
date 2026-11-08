from parking.services.parking_service import ParkingService


class ParkingController:
    @staticmethod
    def vehicle_list():
        return ParkingService.get_parked_vehicles()