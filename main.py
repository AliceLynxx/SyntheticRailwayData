#!/usr/bin/env python3
"""
Hoofdscript voor het genereren van synthetische spoorwegonderhoudsdata.

Dit script orkestreert het volledige proces van het genereren van realistische
onderhoudsdata voor het Nederlandse spoorwegnetwerk, inclusief stationsdata,
wisselonderhoud en export naar CSV formaat.

Gebruik:
    python main.py [--records N] [--output filename.csv] [--verbose]

Auteur: SyntheticRailwayData Project
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Import van onze modules
from data_generation.station_loader import load_station_data, validate_station_data
from data_generation.maintenance_generator import generate_maintenance_records
from data_generation.data_exporter import export_to_csv, validate_export_data
from constants import DEFAULT_RECORD_COUNT


def setup_logging(verbose=False):
    """
    Configureer logging voor het applicatie.
    
    Args:
        verbose (bool): Als True, zet logging level op DEBUG
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configureer logging formaat
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger configuratie
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(console_handler)
    
    # Log file handler (optioneel)
    log_file = Path('synthetic_railway_data.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def parse_arguments():
    """
    Parse command line argumenten.
    
    Returns:
        argparse.Namespace: Geparseerde argumenten
    """
    parser = argparse.ArgumentParser(
        description='Genereer synthetische spoorwegonderhoudsdata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
    python main.py                              # Genereer 1000 records (default)
    python main.py --records 5000               # Genereer 5000 records
    python main.py --output my_data.csv         # Specificeer output bestand
    python main.py --records 2000 --verbose     # Uitgebreide logging
        """
    )
    
    parser.add_argument(
        '--records', '-r',
        type=int,
        default=DEFAULT_RECORD_COUNT,
        help=f'Aantal onderhoudsrecords te genereren (default: {DEFAULT_RECORD_COUNT})'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='synthetic_maintenance_data.csv',
        help='Output CSV bestandsnaam (default: synthetic_maintenance_data.csv)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Uitgebreide logging (DEBUG level)'
    )
    
    parser.add_argument(
        '--no-validation',
        action='store_true',
        help='Sla data validatie over (sneller, maar minder veilig)'
    )
    
    return parser.parse_args()


def main():
    """
    Hoofdfunctie die het volledige generatieproces orkestreert.
    """
    # Parse argumenten
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    logger.info("=== Synthetische Spoorwegonderhoudsdata Generator ===")
    logger.info(f"Start tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Aantal records te genereren: {args.records:,}")
    logger.info(f"Output bestand: {args.output}")
    
    try:
        # Stap 1: Laad stationsdata
        logger.info("Stap 1/4: Laden van stationsdata...")
        station_data = load_station_data()
        
        if not args.no_validation:
            logger.info("Valideren van stationsdata...")
            validate_station_data(station_data)
        
        logger.info(f"Stationsdata geladen: {len(station_data)} stations beschikbaar")
        
        # Stap 2: Genereer onderhoudsrecords
        logger.info("Stap 2/4: Genereren van onderhoudsrecords...")
        maintenance_records = generate_maintenance_records(
            station_data=station_data,
            num_records=args.records
        )
        
        logger.info(f"Onderhoudsrecords gegenereerd: {len(maintenance_records)} records")
        
        # Stap 3: Valideer gegenereerde data (optioneel)
        if not args.no_validation:
            logger.info("Stap 3/4: Valideren van gegenereerde data...")
            validate_export_data(maintenance_records)
            logger.info("Data validatie succesvol")
        else:
            logger.info("Stap 3/4: Data validatie overgeslagen")
        
        # Stap 4: Exporteer naar CSV
        logger.info("Stap 4/4: Exporteren naar CSV...")
        export_result = export_to_csv(
            data=maintenance_records,
            filename=args.output
        )
        
        # Resultaat rapportage
        logger.info("=== Generatie Voltooid ===")
        logger.info(f"Output bestand: {export_result['filename']}")
        logger.info(f"Bestandsgrootte: {export_result['file_size_mb']:.2f} MB")
        logger.info(f"Aantal records: {export_result['record_count']:,}")
        logger.info(f"Aantal unieke stations: {export_result['unique_stations']}")
        logger.info(f"Aantal unieke wissels: {export_result['unique_switches']}")
        logger.info(f"Datum range: {export_result['date_range']['start']} tot {export_result['date_range']['end']}")
        logger.info(f"Eind tijd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n✅ Synthetische onderhoudsdata succesvol gegenereerd!")
        print(f"📁 Bestand: {args.output}")
        print(f"📊 Records: {export_result['record_count']:,}")
        print(f"💾 Grootte: {export_result['file_size_mb']:.2f} MB")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Proces onderbroken door gebruiker")
        return 1
        
    except Exception as e:
        logger.error(f"Fout tijdens generatie: {str(e)}")
        logger.debug("Volledige error traceback:", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
