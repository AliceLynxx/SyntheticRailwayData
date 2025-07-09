"""
Module voor het genereren van synthetische onderhoudsrecords.

Deze module genereert realistische onderhoudsdata voor spoorwegwissels,
waarbij consistentie wordt gewaarborgd voor switch eigenschappen en
realistische waarden worden toegewezen op basis van constants.py.
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
from tqdm import tqdm

from constants import (
    SWITCH_TYPES, SWITCH_HANDS, MAINTENANCE_TYPES, MAINTENANCE_CATEGORIES,
    WORK_DESCRIPTIONS, BLADE_CONDITIONS, CONTRACTOR_COMPANIES,
    UNIQUE_SWITCH_COUNT, get_random_duration, get_random_wear_measurement,
    get_random_technician_count, should_apply_lubrication, should_service_motor,
    get_random_test_result, get_random_work_time, get_random_date,
    MAINTENANCE_PATTERNS
)

logger = logging.getLogger(__name__)


class SwitchRegistry:
    """
    Registry voor het bijhouden van consistente switch eigenschappen.
    
    Zorgt ervoor dat elke switch_id altijd dezelfde eigenschappen heeft
    zoals switch_type, switch_hand, station_code en station_name.
    """
    
    def __init__(self, station_data: List[Dict[str, Any]]):
        """
        Initialiseer de switch registry.
        
        Args:
            station_data: Lijst met beschikbare stations
        """
        self.station_data = station_data
        self.switches: Dict[str, Dict[str, Any]] = {}
        self._used_switch_ids: Set[str] = set()
        
        logger.info(f"Switch registry geïnitialiseerd met {len(station_data)} stations")
    
    def get_or_create_switch(self, switch_id: str = None) -> Dict[str, Any]:
        """
        Haal bestaande switch op of creëer nieuwe switch met consistente eigenschappen.
        
        Args:
            switch_id: Optionele switch ID. Als None, wordt nieuwe ID gegenereerd.
            
        Returns:
            Dict met switch eigenschappen: switch_id, switch_type, switch_hand,
            station_code, station_name
        """
        if switch_id is None:
            switch_id = self._generate_unique_switch_id()
        
        if switch_id not in self.switches:
            self.switches[switch_id] = self._create_switch_properties(switch_id)
            logger.debug(f"Nieuwe switch aangemaakt: {switch_id}")
        
        return self.switches[switch_id].copy()
    
    def _generate_unique_switch_id(self) -> str:
        """
        Genereer unieke switch ID.
        
        Returns:
            Unieke switch ID string
        """
        while True:
            # Genereer switch ID in formaat: SW-XXXX (bijv. SW-0001)
            switch_id = f"SW-{random.randint(1, UNIQUE_SWITCH_COUNT * 2):04d}"
            
            if switch_id not in self._used_switch_ids:
                self._used_switch_ids.add(switch_id)
                return switch_id
    
    def _create_switch_properties(self, switch_id: str) -> Dict[str, Any]:
        """
        Creëer consistente eigenschappen voor een nieuwe switch.
        
        Args:
            switch_id: Switch ID
            
        Returns:
            Dict met switch eigenschappen
        """
        # Selecteer willekeurig station
        station = random.choice(self.station_data)
        
        # Bepaal switch eigenschappen
        switch_type = random.choice(SWITCH_TYPES)
        switch_hand = random.choice(SWITCH_HANDS)
        
        # Pas specialisatie patronen toe
        switch_type = self._apply_specialization_patterns(switch_type, station)
        
        return {
            'switch_id': switch_id,
            'switch_type': switch_type,
            'switch_hand': switch_hand,
            'station_code': station['station_code'],
            'station_name': station['station_name']
        }
    
    def _apply_specialization_patterns(self, switch_type: str, station: Dict[str, Any]) -> str:
        """
        Pas specialisatie patronen toe voor realistische verdeling.
        
        Args:
            switch_type: Oorspronkelijk switch type
            station: Station informatie
            
        Returns:
            Mogelijk aangepast switch type
        """
        patterns = MAINTENANCE_PATTERNS.get('high_maintenance_switches', {})
        high_maintenance_types = patterns.get('switch_types', [])
        
        # Grotere stations hebben meer complexe wissels
        major_stations = ['AMS', 'RTD', 'UTR', 'EHV', 'AH']
        
        if station['station_code'] in major_stations:
            # 40% kans op complexere wissel bij grote stations
            if random.random() < 0.4 and high_maintenance_types:
                return random.choice(high_maintenance_types)
        
        return switch_type
    
    def get_switch_count(self) -> int:
        """
        Geef aantal geregistreerde switches terug.
        
        Returns:
            Aantal switches in registry
        """
        return len(self.switches)
    
    def get_all_switches(self) -> List[Dict[str, Any]]:
        """
        Geef alle geregistreerde switches terug.
        
        Returns:
            Lijst met alle switch eigenschappen
        """
        return list(self.switches.values())


def generate_maintenance_records(station_data: List[Dict[str, Any]], 
                               num_records: int) -> List[Dict[str, Any]]:
    """
    Genereer synthetische onderhoudsrecords.
    
    Args:
        station_data: Lijst met beschikbare stations
        num_records: Aantal records te genereren
        
    Returns:
        Lijst met onderhoudsrecords
        
    Raises:
        ValueError: Als ongeldige parameters worden gegeven
    """
    logger.info(f"Start generatie van {num_records:,} onderhoudsrecords...")
    
    if not station_data:
        raise ValueError("Stationsdata is leeg")
    
    if num_records <= 0:
        raise ValueError("Aantal records moet positief zijn")
    
    # Initialiseer switch registry
    switch_registry = SwitchRegistry(station_data)
    
    # Genereer records met progress bar
    records = []
    
    with tqdm(total=num_records, desc="Genereren records", unit="records") as pbar:
        for i in range(num_records):
            try:
                record = generate_single_record(switch_registry)
                records.append(record)
                pbar.update(1)
                
                # Log progress elke 1000 records
                if (i + 1) % 1000 == 0:
                    logger.debug(f"Gegenereerd: {i + 1:,} records")
                    
            except Exception as e:
                logger.error(f"Fout bij genereren record {i + 1}: {e}")
                raise
    
    logger.info(f"Generatie voltooid: {len(records):,} records")
    logger.info(f"Unieke switches gebruikt: {switch_registry.get_switch_count()}")
    
    return records


def generate_single_record(switch_registry: SwitchRegistry) -> Dict[str, Any]:
    """
    Genereer één onderhoudsrecord.
    
    Args:
        switch_registry: Switch registry voor consistente eigenschappen
        
    Returns:
        Dict met onderhoudsrecord
    """
    # Bepaal of we bestaande switch gebruiken of nieuwe aanmaken
    use_existing_switch = (
        switch_registry.get_switch_count() > 0 and 
        random.random() < 0.7  # 70% kans op hergebruik bestaande switch
    )
    
    if use_existing_switch:
        # Selecteer willekeurige bestaande switch
        existing_switches = switch_registry.get_all_switches()
        switch_info = random.choice(existing_switches)
        switch_info = switch_registry.get_or_create_switch(switch_info['switch_id'])
    else:
        # Creëer nieuwe switch
        switch_info = switch_registry.get_or_create_switch()
    
    # Genereer basis record informatie
    maintenance_id = str(uuid.uuid4())
    maintenance_type = random.choice(MAINTENANCE_TYPES)
    maintenance_category = random.choice(MAINTENANCE_CATEGORIES)
    
    # Genereer datum en tijd
    maintenance_date = get_random_date()
    maintenance_time = get_random_work_time()
    
    # Pas seizoensgebonden patronen toe
    maintenance_date = _apply_seasonal_patterns(maintenance_date, maintenance_type)
    
    # Genereer realistische waarden
    duration_minutes = get_random_duration(maintenance_type)
    work_description = random.choice(WORK_DESCRIPTIONS)
    blade_condition = random.choice(BLADE_CONDITIONS)
    wear_measurement = get_random_wear_measurement()
    technician_count = get_random_technician_count()
    
    # Bepaal boolean waarden op basis van onderhoudstype
    lubrication_applied = should_apply_lubrication(maintenance_type)
    point_motor_serviced = should_service_motor(maintenance_type)
    
    # Selecteer contractor op basis van specialisatie
    contractor_company = _select_contractor(switch_info['switch_type'])
    
    # Genereer test resultaat
    switch_operation_test = get_random_test_result()
    
    # Bouw record samen
    record = {
        'maintenance_id': maintenance_id,
        'station_code': switch_info['station_code'],
        'station_name': switch_info['station_name'],
        'switch_id': switch_info['switch_id'],
        'switch_type': switch_info['switch_type'],
        'switch_hand': switch_info['switch_hand'],
        'date': maintenance_date.strftime('%Y-%m-%d'),
        'time': maintenance_time,
        'duration_minutes': duration_minutes,
        'maintenance_type': maintenance_type,
        'maintenance_category': maintenance_category,
        'work_description': work_description,
        'lubrication_applied': lubrication_applied,
        'point_motor_serviced': point_motor_serviced,
        'blade_condition': blade_condition,
        'wear_measurement_mm': wear_measurement,
        'technician_count': technician_count,
        'contractor_company': contractor_company,
        'switch_operation_test': switch_operation_test
    }
    
    return record


def _apply_seasonal_patterns(date: datetime, maintenance_type: str) -> datetime:
    """
    Pas seizoensgebonden onderhoudspatronen toe.
    
    Args:
        date: Oorspronkelijke datum
        maintenance_type: Type onderhoud
        
    Returns:
        Mogelijk aangepaste datum
    """
    seasonal_config = MAINTENANCE_PATTERNS.get('seasonal_maintenance', {})
    
    winter_months = seasonal_config.get('winter_months', [])
    summer_months = seasonal_config.get('summer_months', [])
    
    month = date.month
    
    # Meer preventief onderhoud in winter
    if (month in winter_months and 
        maintenance_type == 'Preventief onderhoud' and 
        random.random() < 0.3):
        # Verschuif naar winter maand
        winter_month = random.choice(winter_months)
        date = date.replace(month=winter_month)
    
    # Minder onderhoud in zomer (vakantieperiode)
    elif (month in summer_months and 
          random.random() < 0.2):
        # Verschuif naar niet-zomer maand
        non_summer_months = [m for m in range(1, 13) if m not in summer_months]
        new_month = random.choice(non_summer_months)
        date = date.replace(month=new_month)
    
    return date


def _select_contractor(switch_type: str) -> str:
    """
    Selecteer contractor op basis van specialisatie patronen.
    
    Args:
        switch_type: Type wissel
        
    Returns:
        Contractor company naam
    """
    specialization = MAINTENANCE_PATTERNS.get('contractor_specialization', {})
    
    # Zoek gespecialiseerde contractors voor dit switch type
    specialized_contractors = []
    for contractor, switch_types in specialization.items():
        if switch_type in switch_types:
            specialized_contractors.append(contractor)
    
    # 60% kans op gespecialiseerde contractor
    if specialized_contractors and random.random() < 0.6:
        return random.choice(specialized_contractors)
    
    # Anders willekeurige contractor
    return random.choice(CONTRACTOR_COMPANIES)


def create_switch_registry(station_data: List[Dict[str, Any]]) -> SwitchRegistry:
    """
    Creëer nieuwe switch registry.
    
    Args:
        station_data: Lijst met beschikbare stations
        
    Returns:
        Nieuwe SwitchRegistry instance
    """
    return SwitchRegistry(station_data)


def assign_realistic_values(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wijs realistische waarden toe aan een record op basis van constants.
    
    Args:
        record: Basis record om aan te vullen
        
    Returns:
        Record met realistische waarden
    """
    # Deze functie kan gebruikt worden voor post-processing
    # van records om extra realisme toe te voegen
    
    maintenance_type = record.get('maintenance_type', 'Preventief onderhoud')
    
    # Pas duur aan op basis van type en complexiteit
    if record.get('switch_type') in ['Kruiswissel', 'Dubbele kruiswissel']:
        # Complexere wissels nemen meer tijd
        record['duration_minutes'] = int(record['duration_minutes'] * 1.3)
    
    # Pas slijtage aan op basis van blade conditie
    blade_condition = record.get('blade_condition', 'Goed')
    if blade_condition in ['Sterke slijtage', 'Vervangen nodig']:
        # Meer slijtage bij slechte conditie
        record['wear_measurement_mm'] = max(
            record['wear_measurement_mm'], 
            random.uniform(15.0, 25.0)
        )
    elif blade_condition == 'Goed':
        # Minder slijtage bij goede conditie
        record['wear_measurement_mm'] = min(
            record['wear_measurement_mm'], 
            random.uniform(0.0, 5.0)
        )
    
    # Pas technician count aan op basis van onderhoud complexiteit
    if maintenance_type in ['Noodonderhoud', 'Correctief onderhoud']:
        # Meer technici bij urgente reparaties
        record['technician_count'] = max(record['technician_count'], 2)
    
    return record