from parking.repositories.vehicle_repository import VehicleRepository


class ParkingService:
    @staticmethod
    def register_vehicle(plate, vehicle_type):
        if not plate or not plate.strip():
            raise ValueError("Davlat raqami kiritilishi kerak")

        if VehicleRepository.find_by_plate(plate):
            raise ValueError("Bu avtomobil avtoturargohda mavjud")

        return VehicleRepository.create(
            plate=plate.strip().upper(),
            vehicle_type=vehicle_type
        )

    @staticmethod
    def get_parked_vehicles():
        return VehicleRepository.get_all()