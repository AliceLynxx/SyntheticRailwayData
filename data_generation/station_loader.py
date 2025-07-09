"""
Module voor het laden en valideren van stationsdata.

Deze module laadt stationsdata uit all_disruptions.csv of creëert fallback data
als het bestand niet beschikbaar is. Het zorgt voor consistente stationsdata
die gebruikt wordt voor het genereren van onderhoudsrecords.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import ast

logger = logging.getLogger(__name__)


def load_station_data() -> List[Dict[str, Any]]:
    """
    Laadt stationsdata uit all_disruptions.csv of creëert fallback data.
    
    Probeert eerst all_disruptions.csv te laden. Als dit niet lukt, wordt
    fallback data gebruikt met de meest voorkomende Nederlandse stations.
    
    Returns:
        List[Dict[str, Any]]: Lijst met station dictionaries met keys:
            - station_code: Stationscode (bijv. 'AMS')
            - station_name: Stationnaam (bijv. 'Amsterdam Centraal')
    
    Raises:
        Exception: Als noch het CSV bestand noch fallback data beschikbaar is
    """
    logger.info("Proberen stationsdata te laden uit all_disruptions.csv...")
    
    # Probeer eerst het CSV bestand te laden
    csv_path = Path('all_disruptions.csv')
    
    if csv_path.exists():
        try:
            station_data = _load_from_csv(csv_path)
            logger.info(f"Stationsdata geladen uit CSV: {len(station_data)} stations")
            return station_data
        except Exception as e:
            logger.warning(f"Fout bij laden CSV bestand: {e}")
            logger.info("Vallen terug op fallback stationsdata...")
    else:
        logger.info("all_disruptions.csv niet gevonden, gebruik fallback data...")
    
    # Gebruik fallback data
    fallback_data = _create_fallback_station_data()
    logger.info(f"Fallback stationsdata aangemaakt: {len(fallback_data)} stations")
    
    return fallback_data


def _load_from_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Laadt stationsdata uit het CSV bestand.
    
    Args:
        csv_path (Path): Pad naar het all_disruptions.csv bestand
        
    Returns:
        List[Dict[str, Any]]: Lijst met unieke stations
        
    Raises:
        Exception: Als het CSV bestand niet gelezen kan worden
    """
    try:
        # Lees CSV bestand
        df = pd.read_csv(csv_path)
        
        # Controleer eerst op nieuwe kolomnamen (rdt_station_names en rdt_station_codes)
        if 'rdt_station_names' in df.columns and 'rdt_station_codes' in df.columns:
            logger.info("Gevonden rdt_station_names en rdt_station_codes kolommen, uitpakken van lijsten...")
            return _extract_stations_from_rdt_columns(df)
        
        # Fallback naar originele logica voor backward compatibility
        logger.info("Geen rdt kolommen gevonden, proberen originele kolomnamen...")
        
        # Controleer of vereiste kolommen aanwezig zijn
        required_columns = ['station_code', 'station_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            # Probeer alternatieve kolomnamen
            column_mapping = {
                'code': 'station_code',
                'name': 'station_name',
                'station': 'station_name',
                'location': 'station_name'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns and new_col in missing_columns:
                    df[new_col] = df[old_col]
                    missing_columns.remove(new_col)
        
        if missing_columns:
            raise ValueError(f"Vereiste kolommen ontbreken: {missing_columns}")
        
        # Haal unieke stations op
        unique_stations = df[['station_code', 'station_name']].drop_duplicates()
        
        # Verwijder lege waarden
        unique_stations = unique_stations.dropna()
        
        # Converteer naar lijst van dictionaries
        station_data = unique_stations.to_dict('records')
        
        # Zorg voor string types
        for station in station_data:
            station['station_code'] = str(station['station_code']).strip()
            station['station_name'] = str(station['station_name']).strip()
        
        return station_data
        
    except Exception as e:
        logger.error(f"Fout bij laden CSV bestand: {e}")
        raise


def _extract_stations_from_rdt_columns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extraheert stationsdata uit rdt_station_names en rdt_station_codes kolommen.
    
    Deze kolommen bevatten lijsten van stationsnamen en -codes die uitgepakt
    moeten worden naar individuele station records.
    
    Args:
        df (pd.DataFrame): DataFrame met rdt_station_names en rdt_station_codes kolommen
        
    Returns:
        List[Dict[str, Any]]: Lijst met unieke stations
    """
    stations = []
    
    for _, row in df.iterrows():
        # Haal station namen en codes op
        station_names = row['rdt_station_names']
        station_codes = row['rdt_station_codes']
        
        # Skip lege waarden
        if pd.isna(station_names) or pd.isna(station_codes):
            continue
        
        # Parse lijsten (kunnen strings zijn die lijsten representeren)
        try:
            if isinstance(station_names, str):
                # Probeer als Python lijst te parsen
                try:
                    station_names = ast.literal_eval(station_names)
                except (ValueError, SyntaxError):
                    # Als dat niet lukt, split op komma's
                    station_names = [name.strip() for name in station_names.split(',')]
            
            if isinstance(station_codes, str):
                # Probeer als Python lijst te parsen
                try:
                    station_codes = ast.literal_eval(station_codes)
                except (ValueError, SyntaxError):
                    # Als dat niet lukt, split op komma's
                    station_codes = [code.strip() for code in station_codes.split(',')]
            
            # Zorg ervoor dat beide lijsten zijn
            if not isinstance(station_names, list):
                station_names = [station_names]
            if not isinstance(station_codes, list):
                station_codes = [station_codes]
            
            # Combineer namen en codes (gebruik de kortste lijst als lengte)
            min_length = min(len(station_names), len(station_codes))
            
            for i in range(min_length):
                name = str(station_names[i]).strip()
                code = str(station_codes[i]).strip()
                
                # Skip lege waarden
                if name and code:
                    stations.append({
                        'station_name': name,
                        'station_code': code
                    })
                    
        except Exception as e:
            logger.warning(f"Fout bij parsen van station data in rij: {e}")
            continue
    
    # Verwijder duplicaten
    unique_stations = []
    seen_codes = set()
    
    for station in stations:
        if station['station_code'] not in seen_codes:
            unique_stations.append(station)
            seen_codes.add(station['station_code'])
    
    logger.info(f"Uitgepakt {len(unique_stations)} unieke stations uit rdt kolommen")
    return unique_stations


def _create_fallback_station_data() -> List[Dict[str, Any]]:
    """
    Creëert fallback stationsdata met de belangrijkste Nederlandse stations.
    
    Returns:
        List[Dict[str, Any]]: Lijst met fallback stations
    """
    fallback_stations = [
        {"station_code": "AMS", "station_name": "Amsterdam Centraal"},
        {"station_code": "RTD", "station_name": "Rotterdam Centraal"},
        {"station_code": "UTR", "station_name": "Utrecht Centraal"},
        {"station_code": "EHV", "station_name": "Eindhoven Centraal"},
        {"station_code": "TIL", "station_name": "Tilburg"},
        {"station_code": "AH", "station_name": "Den Haag Centraal"},
        {"station_code": "GVC", "station_name": "Den Haag HS"},
        {"station_code": "AMF", "station_name": "Amersfoort Centraal"},
        {"station_code": "ZWO", "station_name": "Zwolle"},
        {"station_code": "LWD", "station_name": "Leeuwarden"},
        {"station_code": "GN", "station_name": "Groningen"},
        {"station_code": "ASS", "station_name": "Assen"},
        {"station_code": "ENS", "station_name": "Enschede"},
        {"station_code": "ZL", "station_name": "Zutphen"},
        {"station_code": "ARN", "station_name": "Arnhem Centraal"},
        {"station_code": "NM", "station_name": "Nijmegen"},
        {"station_code": "VB", "station_name": "Venlo"},
        {"station_code": "MR", "station_name": "Maastricht"},
        {"station_code": "SHL", "station_name": "Schiphol Airport"},
        {"station_code": "AMSA", "station_name": "Amsterdam Amstel"},
        {"station_code": "AMSS", "station_name": "Amsterdam Sloterdijk"},
        {"station_code": "AMSO", "station_name": "Amsterdam Zuid"},
        {"station_code": "BD", "station_name": "Breda"},
        {"station_code": "DV", "station_name": "Deventer"},
        {"station_code": "HLM", "station_name": "Haarlem"},
        {"station_code": "LLS", "station_name": "Lelystad Centrum"},
        {"station_code": "AKM", "station_name": "Alkmaar"},
        {"station_code": "HRN", "station_name": "Hoorn"},
        {"station_code": "ZD", "station_name": "Zaandam"},
        {"station_code": "HTNC", "station_name": "Houten Castellum"},
        {"station_code": "GDA", "station_name": "Gouda"},
        {"station_code": "DT", "station_name": "Delft"},
        {"station_code": "SDM", "station_name": "Schiedam Centrum"},
        {"station_code": "VLI", "station_name": "Vlissingen"},
        {"station_code": "MDL", "station_name": "Middelburg"},
        {"station_code": "RSD", "station_name": "Roosendaal"},
        {"station_code": "DRD", "station_name": "Dordrecht"},
        {"station_code": "MT", "station_name": "Maastricht"},
        {"station_code": "SIT", "station_name": "Sittard"},
        {"station_code": "HRL", "station_name": "Heerlen"},
        {"station_code": "KRD", "station_name": "Kerkrade Centrum"},
        {"station_code": "HM", "station_name": "Helmond"},
        {"station_code": "OSS", "station_name": "Oss"},
        {"station_code": "HT", "station_name": "'s-Hertogenbosch"},
        {"station_code": "TB", "station_name": "Tiel"},
        {"station_code": "WG", "station_name": "Wageningen"},
        {"station_code": "ED", "station_name": "Ede-Wageningen"},
        {"station_code": "BKL", "station_name": "Barneveld Centrum"},
        {"station_code": "HVS", "station_name": "Harderwijk"},
        {"station_code": "KMP", "station_name": "Kampen"},
        {"station_code": "MPN", "station_name": "Meppel"},
        {"station_code": "HGL", "station_name": "Hoogeveen"},
        {"station_code": "EMN", "station_name": "Emmen"},
        {"station_code": "WZ", "station_name": "Winschoten"},
        {"station_code": "VRN", "station_name": "Veendam"},
        {"station_code": "STD", "station_name": "Stadskanaal"},
        {"station_code": "BES", "station_name": "Beilen"},
        {"station_code": "DKL", "station_name": "Drachten"},
        {"station_code": "HRD", "station_name": "Heerenveen"},
        {"station_code": "SNK", "station_name": "Sneek"},
        {"station_code": "FRN", "station_name": "Franeker"},
        {"station_code": "HNS", "station_name": "Harlingen Haven"},
        {"station_code": "DEN", "station_name": "Den Helder"},
        {"station_code": "SGN", "station_name": "Schagen"},
        {"station_code": "HFD", "station_name": "Heerhugowaard"},
        {"station_code": "CPS", "station_name": "Castricum"},
        {"station_code": "BV", "station_name": "Beverwijk"},
        {"station_code": "KRG", "station_name": "Krommenie-Assendelft"},
        {"station_code": "WM", "station_name": "Wormerveer"},
        {"station_code": "KG", "station_name": "Koog aan de Zaan"},
        {"station_code": "ZSS", "station_name": "Zaandam Kogerveld"},
        {"station_code": "PU", "station_name": "Purmerend"},
        {"station_code": "HVD", "station_name": "Hoorn Kersenboogerd"},
        {"station_code": "EDN", "station_name": "Enkhuizen"},
        {"station_code": "BOV", "station_name": "Bovenkarspel-Grootebroek"},
        {"station_code": "HN", "station_name": "Houten"},
        {"station_code": "CL", "station_name": "Culemborg"},
        {"station_code": "TB", "station_name": "Tiel"},
        {"station_code": "ELT", "station_name": "Elst"},
        {"station_code": "LCH", "station_name": "Leerdam"},
        {"station_code": "GOR", "station_name": "Gorinchem"},
        {"station_code": "BT", "station_name": "Beesd"},
        {"station_code": "GEL", "station_name": "Geldermalsen"},
        {"station_code": "ZBM", "station_name": "Zaltbommel"},
        {"station_code": "HDB", "station_name": "Hedel"},
        {"station_code": "RV", "station_name": "Ravenstein"},
        {"station_code": "OHT", "station_name": "Oss West"},
        {"station_code": "VGH", "station_name": "Veghel"},
        {"station_code": "BXL", "station_name": "Boxtel"},
        {"station_code": "BST", "station_name": "Best"},
        {"station_code": "EHB", "station_name": "Eindhoven Beukenlaan"},
        {"station_code": "GLD", "station_name": "Geldrop"},
        {"station_code": "HZB", "station_name": "Heeze"},
        {"station_code": "WVB", "station_name": "Weert"},
        {"station_code": "RRM", "station_name": "Roermond"},
        {"station_code": "VLO", "station_name": "Venlo"},
        {"station_code": "TGM", "station_name": "Tegelen"},
        {"station_code": "RMD", "station_name": "Reuver"},
        {"station_code": "SV", "station_name": "Swalmen"},
        {"station_code": "RRM", "station_name": "Roermond"},
        {"station_code": "EHT", "station_name": "Echt"},
        {"station_code": "SUS", "station_name": "Susteren"},
        {"station_code": "ELD", "station_name": "Elsloo"},
        {"station_code": "ST", "station_name": "Stein-Elsloo"},
        {"station_code": "GVN", "station_name": "Geleen Oost"},
        {"station_code": "SPK", "station_name": "Spaubeek"},
        {"station_code": "BK", "station_name": "Beek-Elsloo"},
        {"station_code": "MH", "station_name": "Meerssen"},
        {"station_code": "HOU", "station_name": "Houthem-St. Gerlach"},
        {"station_code": "VK", "station_name": "Valkenburg"},
        {"station_code": "SC", "station_name": "Schin op Geul"},
        {"station_code": "KLB", "station_name": "Klimmen-Ransdaal"},
        {"station_code": "CHV", "station_name": "Chevremont"},
        {"station_code": "LDG", "station_name": "Landgraaf"},
        {"station_code": "EYG", "station_name": "Eygelshoven"},
        {"station_code": "HOP", "station_name": "Hoensbroek"},
        {"station_code": "NKD", "station_name": "Nuth"},
        {"station_code": "SCH", "station_name": "Schinnen"}
    ]
    
    return fallback_stations


def validate_station_data(station_data: List[Dict[str, Any]]) -> None:
    """
    Valideert de geladen stationsdata.
    
    Args:
        station_data (List[Dict[str, Any]]): Te valideren stationsdata
        
    Raises:
        ValueError: Als de data niet voldoet aan de vereisten
    """
    logger.info("Valideren van stationsdata...")
    
    if not station_data:
        raise ValueError("Stationsdata is leeg")
    
    if not isinstance(station_data, list):
        raise ValueError("Stationsdata moet een lijst zijn")
    
    # Controleer elke station entry
    required_keys = {'station_code', 'station_name'}
    station_codes = set()
    
    for i, station in enumerate(station_data):
        if not isinstance(station, dict):
            raise ValueError(f"Station {i} is geen dictionary")
        
        # Controleer vereiste keys
        missing_keys = required_keys - set(station.keys())
        if missing_keys:
            raise ValueError(f"Station {i} mist keys: {missing_keys}")
        
        # Controleer data types en inhoud
        station_code = station['station_code']
        station_name = station['station_name']
        
        if not isinstance(station_code, str) or not station_code.strip():
            raise ValueError(f"Station {i} heeft ongeldige station_code: {station_code}")
        
        if not isinstance(station_name, str) or not station_name.strip():
            raise ValueError(f"Station {i} heeft ongeldige station_name: {station_name}")
        
        # Controleer op duplicaten
        if station_code in station_codes:
            raise ValueError(f"Duplicate station_code gevonden: {station_code}")
        
        station_codes.add(station_code)
    
    logger.info(f"Stationsdata validatie succesvol: {len(station_data)} unieke stations")
    
    # Log statistieken
    logger.debug(f"Station codes: {sorted(list(station_codes))}")
    logger.debug(f"Langste station naam: {max(station['station_name'] for station in station_data)}")
    logger.debug(f"Kortste station code: {min(station['station_code'] for station in station_data)}")