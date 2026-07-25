import sys

import shutil

import logging

from pathlib import Path

logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",

    handlers=[logging.StreamHandler(sys.stdout)],

)

logger = logging.getLogger("byepii.cli")

import config

from core.pipeline import ByePIIPipeline

def main():

    if len(sys.argv) >= 2:

        input_arg = sys.argv[1]

    else:

        input_arg = "input.docx"

    if len(sys.argv) >= 3:

        output_arg = sys.argv[2]

    else:

        input_p = Path(input_arg)

        output_arg = str(input_p.parent / f"output{input_p.suffix}")

    input_path = Path(input_arg)

    output_path = Path(output_arg)

    if not input_path.exists():

        input_path = config.BASE_DIR / input_arg

        if not input_path.exists():

            logger.error(f"Input file not found: {input_arg}")

            sys.exit(1)

    logger.info(f"Input  : {input_path}")

    logger.info(f"Output : {output_path}")

    logger.info("Initializing ByePII pipeline (this may take a moment to load models)...")

    pipeline = ByePIIPipeline()

    logger.info("Running redaction pipeline...")

    result = pipeline.process_file(str(input_path))

    redacted_path = result.get("redacted_file_path")

    if not redacted_path or not Path(redacted_path).exists():

        logger.error(f"Pipeline did not produce an output file. result={result}")

        sys.exit(1)

    shutil.copy2(redacted_path, output_path)

    logger.info(f"Redacted document saved to: {output_path}")

    entities = result.get("entities", [])

    logger.info(f"Total entities detected and redacted: {len(entities)}")

    label_counts: dict = {}

    for ent in entities:

        lbl = ent.get("label", "UNKNOWN")

        label_counts[lbl] = label_counts.get(lbl, 0) + 1

    if label_counts:

        logger.info("Entity breakdown:")

        for lbl, count in sorted(label_counts.items()):

            logger.info(f"  {lbl}: {count}")

    logger.info("Done.")

if __name__ == "__main__":

    main()
