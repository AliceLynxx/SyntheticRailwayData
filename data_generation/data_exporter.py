"""
Module voor het exporteren van synthetische onderhoudsdata.

Deze module exporteert gegenereerde onderhoudsdata naar CSV formaat
en voert validatie uit om data kwaliteit te waarborgen.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def export_to_csv(data: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
    """
    Exporteer onderhoudsdata naar CSV bestand.
    
    Args:
        data: Lijst met onderhoudsrecords
        filename: Naam van het output CSV bestand
        
    Returns:
        Dict met export resultaat informatie:
            - filename: Pad naar het gemaakte bestand
            - record_count: Aantal geëxporteerde records
            - file_size_mb: Bestandsgrootte in MB
            - unique_stations: Aantal unieke stations
            - unique_switches: Aantal unieke wissels
            - date_range: Dict met start en eind datum
            
    Raises:
        Exception: Als export mislukt
    """
    logger.info(f"Start export van {len(data):,} records naar {filename}")
    
    try:
        # Converteer naar DataFrame
        df = pd.DataFrame(data)
        
        if df.empty:
            raise ValueError("Geen data om te exporteren")
        
        # Sorteer op datum en tijd voor betere leesbaarheid
        df['datetime_sort'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        df = df.sort_values('datetime_sort').drop('datetime_sort', axis=1)
        
        # Zorg voor juiste kolom volgorde
        column_order = [
            'maintenance_id', 'station_code', 'station_name', 'switch_id',
            'switch_type', 'switch_hand', 'date', 'time', 'duration_minutes',
            'maintenance_type', 'maintenance_category', 'work_description',
            'lubrication_applied', 'point_motor_serviced', 'blade_condition',
            'wear_measurement_mm', 'technician_count', 'contractor_company',
            'switch_operation_test'
        ]
        
        # Herorden kolommen (behoud extra kolommen die mogelijk bestaan)
        existing_columns = [col for col in column_order if col in df.columns]
        extra_columns = [col for col in df.columns if col not in column_order]
        final_columns = existing_columns + extra_columns
        
        df = df[final_columns]
        
        # Exporteer naar CSV
        output_path = Path(filename)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        # Bereken statistieken
        file_size_bytes = output_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        unique_stations = df['station_code'].nunique()
        unique_switches = df['switch_id'].nunique()
        
        # Datum range
        dates = pd.to_datetime(df['date'])
        date_range = {
            'start': dates.min().strftime('%Y-%m-%d'),
            'end': dates.max().strftime('%Y-%m-%d')
        }
        
        result = {
            'filename': str(output_path.absolute()),
            'record_count': len(df),
            'file_size_mb': file_size_mb,
            'unique_stations': unique_stations,
            'unique_switches': unique_switches,
            'date_range': date_range
        }
        
        logger.info(f"Export succesvol voltooid:")
        logger.info(f"  - Bestand: {result['filename']}")
        logger.info(f"  - Records: {result['record_count']:,}")
        logger.info(f"  - Grootte: {result['file_size_mb']:.2f} MB")
        logger.info(f"  - Unieke stations: {result['unique_stations']}")
        logger.info(f"  - Unieke wissels: {result['unique_switches']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Fout bij export naar CSV: {e}")
        raise


def validate_export_data(data: List[Dict[str, Any]]) -> None:
    """
    Valideer data voor export om kwaliteit te waarborgen.
    
    Args:
        data: Te valideren onderhoudsdata
        
    Raises:
        ValueError: Als data niet voldoet aan kwaliteitseisen
    """
    logger.info("Start validatie van export data...")
    
    if not data:
        raise ValueError("Geen data om te valideren")
    
    if not isinstance(data, list):
        raise ValueError("Data moet een lijst zijn")
    
    # Vereiste kolommen
    required_columns = {
        'maintenance_id', 'station_code', 'station_name', 'switch_id',
        'switch_type', 'switch_hand', 'date', 'time', 'duration_minutes',
        'maintenance_type', 'maintenance_category', 'work_description',
        'lubrication_applied', 'point_motor_serviced', 'blade_condition',
        'wear_measurement_mm', 'technician_count', 'contractor_company',
        'switch_operation_test'
    }
    
    # Valideer elk record
    maintenance_ids = set()
    
    for i, record in enumerate(data):
        if not isinstance(record, dict):
            raise ValueError(f"Record {i} is geen dictionary")
        
        # Controleer vereiste kolommen
        missing_columns = required_columns - set(record.keys())
        if missing_columns:
            raise ValueError(f"Record {i} mist kolommen: {missing_columns}")
        
        # Valideer maintenance_id uniciteit
        maintenance_id = record['maintenance_id']
        if maintenance_id in maintenance_ids:
            raise ValueError(f"Duplicate maintenance_id gevonden: {maintenance_id}")
        maintenance_ids.add(maintenance_id)
        
        # Valideer data types en waarden
        _validate_record_values(record, i)
    
    # Valideer data consistentie
    _validate_data_consistency(data)
    
    logger.info(f"Data validatie succesvol: {len(data):,} records gevalideerd")


def _validate_record_values(record: Dict[str, Any], record_index: int) -> None:
    """
    Valideer waarden in een individueel record.
    
    Args:
        record: Te valideren record
        record_index: Index van het record (voor error reporting)
        
    Raises:
        ValueError: Als waarden niet geldig zijn
    """
    # String velden
    string_fields = [
        'maintenance_id', 'station_code', 'station_name', 'switch_id',
        'switch_type', 'switch_hand', 'date', 'time', 'maintenance_type',
        'maintenance_category', 'work_description', 'blade_condition',
        'contractor_company', 'switch_operation_test'
    ]
    
    for field in string_fields:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Record {record_index}: {field} moet een niet-lege string zijn")
    
    # Numerieke velden
    duration = record.get('duration_minutes')
    if not isinstance(duration, (int, float)) or duration <= 0:
        raise ValueError(f"Record {record_index}: duration_minutes moet positief getal zijn")
    
    wear = record.get('wear_measurement_mm')
    if not isinstance(wear, (int, float)) or wear < 0:
        raise ValueError(f"Record {record_index}: wear_measurement_mm moet niet-negatief zijn")
    
    technicians = record.get('technician_count')
    if not isinstance(technicians, int) or technicians <= 0:
        raise ValueError(f"Record {record_index}: technician_count moet positief integer zijn")
    
    # Boolean velden
    bool_fields = ['lubrication_applied', 'point_motor_serviced']
    for field in bool_fields:
        value = record.get(field)
        if not isinstance(value, bool):
            raise ValueError(f"Record {record_index}: {field} moet boolean zijn")
    
    # Datum validatie
    try:
        datetime.strptime(record['date'], '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Record {record_index}: date moet YYYY-MM-DD formaat hebben")
    
    # Tijd validatie
    try:
        datetime.strptime(record['time'], '%H:%M')
    except ValueError:
        raise ValueError(f"Record {record_index}: time moet HH:MM formaat hebben")


def _validate_data_consistency(data: List[Dict[str, Any]]) -> None:
    """
    Valideer consistentie van data tussen records.
    
    Args:
        data: Volledige dataset
        
    Raises:
        ValueError: Als inconsistenties worden gevonden
    """
    logger.debug("Valideren van data consistentie...")
    
    # Track switch eigenschappen voor consistentie
    switch_properties = {}
    
    for record in data:
        switch_id = record['switch_id']
        
        if switch_id not in switch_properties:
            switch_properties[switch_id] = {
                'switch_type': record['switch_type'],
                'switch_hand': record['switch_hand'],
                'station_code': record['station_code'],
                'station_name': record['station_name']
            }
        else:
            # Controleer consistentie
            stored = switch_properties[switch_id]
            
            if stored['switch_type'] != record['switch_type']:
                raise ValueError(
                    f"Inconsistente switch_type voor {switch_id}: "
                    f"{stored['switch_type']} vs {record['switch_type']}"
                )
            
            if stored['switch_hand'] != record['switch_hand']:
                raise ValueError(
                    f"Inconsistente switch_hand voor {switch_id}: "
                    f"{stored['switch_hand']} vs {record['switch_hand']}"
                )
            
            if stored['station_code'] != record['station_code']:
                raise ValueError(
                    f"Inconsistente station_code voor {switch_id}: "
                    f"{stored['station_code']} vs {record['station_code']}"
                )
            
            if stored['station_name'] != record['station_name']:
                raise ValueError(
                    f"Inconsistente station_name voor {switch_id}: "
                    f"{stored['station_name']} vs {record['station_name']}"
                )
    
    logger.debug(f"Consistentie validatie succesvol: {len(switch_properties)} unieke wissels")


def export_to_excel(data: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
    """
    Exporteer onderhoudsdata naar Excel bestand (optionele functionaliteit).
    
    Args:
        data: Lijst met onderhoudsrecords
        filename: Naam van het output Excel bestand
        
    Returns:
        Dict met export resultaat informatie
        
    Raises:
        ImportError: Als openpyxl niet beschikbaar is
        Exception: Als export mislukt
    """
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl is vereist voor Excel export. Installeer met: pip install openpyxl")
    
    logger.info(f"Start Excel export van {len(data):,} records naar {filename}")
    
    try:
        # Converteer naar DataFrame
        df = pd.DataFrame(data)
        
        # Sorteer op datum en tijd
        df['datetime_sort'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        df = df.sort_values('datetime_sort').drop('datetime_sort', axis=1)
        
        # Exporteer naar Excel met formatting
        output_path = Path(filename)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Maintenance_Data', index=False)
            
            # Optioneel: voeg samenvatting sheet toe
            summary_data = {
                'Metric': [
                    'Total Records',
                    'Unique Stations',
                    'Unique Switches',
                    'Date Range Start',
                    'Date Range End',
                    'Export Date'
                ],
                'Value': [
                    len(df),
                    df['station_code'].nunique(),
                    df['switch_id'].nunique(),
                    df['date'].min(),
                    df['date'].max(),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Bereken statistieken
        file_size_bytes = output_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        result = {
            'filename': str(output_path.absolute()),
            'record_count': len(df),
            'file_size_mb': file_size_mb,
            'unique_stations': df['station_code'].nunique(),
            'unique_switches': df['switch_id'].nunique(),
            'date_range': {
                'start': df['date'].min(),
                'end': df['date'].max()
            }
        }
        
        logger.info(f"Excel export succesvol voltooid: {result['filename']}")
        return result
        
    except Exception as e:
        logger.error(f"Fout bij Excel export: {e}")
        raise


def create_data_summary(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Creëer samenvatting van de gegenereerde data.
    
    Args:
        data: Onderhoudsdata
        
    Returns:
        Dict met data samenvatting
    """
    if not data:
        return {'error': 'Geen data beschikbaar'}
    
    df = pd.DataFrame(data)
    
    summary = {
        'total_records': len(df),
        'unique_stations': df['station_code'].nunique(),
        'unique_switches': df['switch_id'].nunique(),
        'date_range': {
            'start': df['date'].min(),
            'end': df['date'].max()
        },
        'maintenance_types': df['maintenance_type'].value_counts().to_dict(),
        'switch_types': df['switch_type'].value_counts().to_dict(),
        'contractors': df['contractor_company'].value_counts().to_dict(),
        'average_duration': df['duration_minutes'].mean(),
        'average_wear': df['wear_measurement_mm'].mean(),
        'lubrication_rate': df['lubrication_applied'].mean(),
        'motor_service_rate': df['point_motor_serviced'].mean()
    }
    
    return summary