from typing import Any, Dict, Optional

import requests
from loguru import logger

import undl.consts as consts


class UNDLClient:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def query(
        self,
        query: str,
        output_format: str = consts.DEFAULT_FORMAT,
        n_results: int = 50,
        offset: int = 0,
        output_file: Optional[str] = None,
    ) -> Any:
        if n_results > 200:
            logger.warning(
                "UN Digital Library only returns up to 200 results per query. Setting n_results to 200."
            )
            n_results = 200

        if output_format not in consts.FORMATS:
            logger.warning(
                f"Format {output_format} not supported. Using {consts.DEFAULT_FORMAT} instead."
            )
            output_format = consts.DEFAULT_FORMAT

        params = {
            "p": query,
            "of": consts.FORMATS[output_format],
            "rg": n_results,
            "c": "Resource Type",
        }

        if offset != 0:
            params["jrec"] = offset + 1

        if self.verbose:
            logger.info(f"Querying UNDL API with params: {params}")

        r = requests.get(consts.BASE_URL, params=params)

        if self.verbose:
            logger.debug(f"URL: {r.url}")

        response = r.content.decode("utf-8")

        with open("tmp.xml", "w") as f:
            f.write(response)

        match output_format:
            case "marcxml":
                response = self.parse_marcxml(xml="tmp.xml", output_file=output_file)
            case _:
                pass

        return response

    def parse_marcxml(self, xml: str, output_file: Optional[str] = None) -> Any:
        from pymarc import parse_xml_to_array

        output = []
        marc_records = parse_xml_to_array(xml)

        for marc_record in marc_records:
            record = {
                "title": marc_record.title(),
                "author": marc_record.author(),
                "isbn": marc_record.isbn(),
                "publisher": marc_record.publisher(),
                "pubyear": marc_record.pubyear(),
                # "location": marc_record.location(),
                # "series": marc_record.series(),
                "downloads": self._get_downloads(marc_record),
                "uniform_title": marc_record.uniformtitle(),
                "subjects": self._get_subjects(marc_record),
            }

            output.append(record)

        if output_file:
            import json

            with open(output_file, "w") as f:
                json.dump(output, f, indent=4, ensure_ascii=False)

    def _get_subjects(self, marc_record: Dict[str, Any]) -> Dict[str, Any]:
        subjects = []
        raw_subjects = marc_record.subjects()

        for raw_subject in raw_subjects:
            subject = raw_subject.subfields_as_dict()
            if subject["2"] == ["unbist"]:
                subjects.extend(subject["a"])

        return subjects

    def _get_downloads(self, marc_record: Dict[str, Any]) -> Dict[str, Any]:
        downloads = []
        raw_downloads = marc_record.get_fields("856")

        for raw_download in raw_downloads:
            download = raw_download.subfields_as_dict()
            if "u" in download and download["u"]:
                downloads.extend(download["u"])

        return downloads
