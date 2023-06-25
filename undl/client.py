import os
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List, Optional

import pymarc
import requests
from loguru import logger
from pymarc import Record

import undl.consts as consts


class UNDLClient:
    """
    Client class for the United Nations Digital Library API.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def query(
        self,
        query: str,
        outputFormat: str = consts.DEFAULT_FORMAT,
        nbResults: int = 50,
        offset: int = 0,
        outputFile: Optional[str] = None,
        oldURL: bool = True,
        apiKey: Optional[str] = os.getenv("UN_API"),
    ) -> Dict[str, Any] | str | None:
        """
        Query the UN Digital Library API.

        Parameters
        ----------
        `query` : `str`
            Query string to search for.
        `outputFormat` : `str`, optional
            Output format _from the API_, by default consts.DEFAULT_FORMAT
        `nbResults` : `int`, optional
            Max. number of results, by default 50
        `offset` : `int`, optional
            Search offset, by default 0
        `outputFile` : `Optional[str]`, optional
            File to which the script will save query results, by default None
        `oldURL` : `bool`, optional
            Use old API URL instead of new one, by default True
        `apiKey` : `Optional[str]`, optional
            API key to use if the script uses the new URL, by default `os.getenv("UN_API")`

        Returns
        -------
        `Dict[str, Any] | str | None`
            _description_
        """

        logger.info(f"Querying UNDL API for query string '{query}'")

        if nbResults > 200:
            logger.warning(
                "UN Digital Library only returns up to 200 results per query. Setting nbResults to 200."
            )
            nbResults = 200

        if outputFormat not in consts.FORMATS:
            logger.warning(
                f"Format {outputFormat} not supported. Using {consts.DEFAULT_FORMAT} instead."
            )
            outputFormat = consts.DEFAULT_FORMAT

        if not apiKey and not oldURL:
            logger.error(
                "No API key found. Please set the UN_API environment variable."
            )
            return None

        params = {
            "p": query,
            "of": consts.FORMATS[outputFormat],
            "rg": nbResults,
            "c": "Resource Type",
        }

        if offset != 0:
            params["jrec"] = offset + 1

        if self.verbose:
            logger.info(f"Querying UNDL API with params: {params}")

        return self._query(
            params=params,
            oldURL=oldURL,
            outputFormat=outputFormat,
            outputFile=outputFile,
            apiKey=apiKey,
        )

    def queryById(
        self,
        recordId: str,
        outputFormat: str = consts.DEFAULT_FORMAT,
        outputFile: Optional[str] = None,
        oldURL: bool = True,
        apiKey: Optional[str] = os.getenv("UN_API"),
    ) -> Dict[str, Any] | str | None:
        """
        Function to query the API for a unique ID.

        Parameters
        ----------
        `id` : `str`
            The id to query for.
        `outputFormat` : `str`, optional
            Output format _from the API_, by default consts.DEFAULT_FORMAT
        `outputFile` : `Optional[str]`, optional
            File to which the script will save the query results, by default None
        `oldURL` : `bool`, optional
            Flag to use the old URL instead of the official one, by default True
        `apiKey` : `Optional[str]`, optional
            API key in the case we use the new URL, by default `os.getenv("UN_API")`

        Returns
        -------
        `Dict[str, Any] | str | None`
            The query results
        """

        logger.info(f"Querying UNDL API for unique ID '{recordId}'")

        if outputFormat not in consts.FORMATS:
            logger.warning(
                f"Format {outputFormat} not supported. Using {consts.DEFAULT_FORMAT} instead."
            )
            outputFormat = consts.DEFAULT_FORMAT

        if not apiKey and not oldURL:
            logger.error(
                "No API key found. Please set the UN_API environment variable."
            )
            return None

        params = {
            "recid": recordId,
            "of": consts.FORMATS[outputFormat],
            "c": "Resource Type",
        }

        if self.verbose:
            logger.info(f"Querying UNDL API with params: {params}")

        return self._query(
            params=params,
            oldURL=oldURL,
            outputFormat=outputFormat,
            outputFile=outputFile,
            apiKey=apiKey,
        )

    def _query(
        self,
        params: Dict[str, Any],
        oldURL: bool = True,
        outputFormat: str = consts.DEFAULT_FORMAT,
        outputFile: Optional[str] = None,
        apiKey: Optional[str] = None,
    ) -> List[Dict[str, Any]] | str | None:
        """
        General query function.

        Parameters
        ----------
        `params` : `Dict[str, Any]`
            Query parameters.
        `oldURL` : `bool`, optional
            Flag to use the old URL or new one, by default True
        `outputFormat` : `Optional[str]`, optional
            Output format – by default MARCXML, by default consts.DEFAULT_FORMAT
        `outputFile` : `Optional[str]`, optional
            File to which the output will be saved, by default None
        `apiKey` : `Optional[str]`, optional
            The API key to use in the case of the new URL, by default None

        Returns
        -------
        `List[Dict[str, Any]] | str | None`
            The query results
        """
        r = requests.get(
            consts.BASE_URL if not oldURL else consts.OLD_BASE_URL,
            params=params,
            headers={
                "Authorization": f"Token {apiKey}",
            }
            if not oldURL
            else None,
        )

        if self.verbose:
            logger.debug(f"URL: {r.url}")

        response = r.content.decode("utf-8")

        tmpFile = NamedTemporaryFile(mode="w")
        tmpFile.write(response)

        match outputFormat:
            case "marcxml":
                parsedResponse = self.parseMARCXML(
                    xml=tmpFile.name, outputFile=outputFile
                )
            case _:
                pass

        logger.success(f"Query successful. Results saved to {outputFile}.")

        return parsedResponse

    def parseMARCXML(
        self,
        xml: str,
        outputFile: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Parse MARCXML to JSON.

        Parameters
        ----------
        `xml` : `str`
            MARCXML string to parse.
        `outputFile` : `Optional[str]`, optional
            File to which the output will be saved, by default `None`.
            In the `None` case, the output will be returned.

        Returns
        -------
        `List[Dict[str, Any]]`
            The parsed MARCXML in a JSON-like format.
        """
        output = []
        records: List[Record] = pymarc.parse_xml_to_array(xml)

        for record in records:
            record = {
                "id": self.extractFromMARC(record, "001"),
                "title": self.extractFromMARC(record, "245"),
                "alt_title": self.extractFromMARC(record, "239"),
                "location": self.extractFromMARC(record, "260", "a"),
                "symbol": self._getSymbol(record),
                "publication_date": self.extractFromMARC(record, "269"),
                "summary": self.extractFromMARC(record, "520"),
                "authors": self.extractFromMARC(
                    record,
                    "710",
                    "a",
                    collection=True,
                ),
                "description": self.extractFromMARC(record, "300"),
                "downloads": self._getDownloads(record),
                "subjects": self._getSubjects(record),
                "agenda": self.extractFromMARC(record, "991"),
                "collections": self._getCollections(record),
                "related_documents": self.extractFromMARC(
                    record,
                    "993",
                    collection=True,
                ),
            }

            # Remove empty fields
            record = {k: v for k, v in record.items() if v}

            output.append(record)

        if outputFile:
            import json

            with open(outputFile, "w") as f:
                json.dump(output, f, indent=4, ensure_ascii=False)

        return output

    def _getSubjects(self, record: Record) -> Dict[str, Any]:
        """
        Helper function to extract subject out of a MARCXML record.

        Parameters
        ----------
        `record` : `Record`
            MARCXML record from which to extract the subjects.

        Returns
        -------
        `Dict[str, Any]`
            The subjects
        """
        subjects: Dict[str, List[str]] = {
            "unbist": [],
            "unbisn": [],
            "misc": [],
        }

        raw_subjects = record.subjects()

        for raw_subject in raw_subjects:
            subject = raw_subject.subfields_as_dict()
            if subject["2"] == ["unbist"]:
                subjects["unbist"].extend(subject["a"])
            elif subject["2"] == ["unbisn"]:
                subjects["unbisn"].extend(subject["a"])
            else:
                subjects["misc"].extend(subject["a"])

        return subjects

    def _getDownloads(self, record: Record) -> Dict[str, Any]:
        """
        Helper function to extract downloads out of a MARCXML record.

        Parameters
        ----------
        `record` : `Record`
            MARCXML record from which to extract the downloads.

        Returns
        -------
        `Dict[str, Any]`
            The downloads
        """
        links: Dict[str, Any] = self.extractFromMARC(
            record,
            "856",
            "u",
            collection=True,
        )

        langs = self.extractFromMARC(
            record,
            "856",
            "y",
            collection=True,
        )

        return {lang: link for lang, link in zip(langs, links)}

    def _getCollections(self, record: Record) -> List[str]:
        """
        Get collections from the MARCXML record.
        See https://research.un.org/en/digitallibrary/export

        Parameters
        ----------
        `record` : `Dict[str, Any]`
            MARCXML record from which to extract the collections.

        Returns
        -------
        `List[str]`
            The collections
        """

        resource_type = record["989"].subfields_as_dict() if "989" in record else {}
        un_bodies = record["981"].subfields_as_dict() if "981" in record else {}

        collections = {
            "resource_type": [v[0] for v in resource_type.values()],
            "un_bodies": [v[0] for v in un_bodies.values()],
        }

        return collections

    def _getSymbol(self, record: Record) -> str | None:
        """
        Get document symbol from the MARCXML record.
        See https://research.un.org/en/digitallibrary/export

        Parameters
        ----------
        `record` : `Dict[str, Any]`
            MARCXML record from which to extract the document symbol.

        Returns
        -------
        `str | None`
            The document symbol
        """

        symbol = self.extractFromMARC(record, "191", "a")

        if not symbol:
            symbol = self.extractFromMARC(record, "791", "a")

        return symbol

    def extractFromMARC(
        self,
        record: Record,
        field: str,
        subfield: Optional[str] = None,
        collection: bool = False,
    ) -> Optional[str | Dict[str, Any]]:
        """
        Extract a field from a MARC record.

        Parameters
        ----------
        `record` : `Dict[str, Any]`
            MARCXML record from which to extract the field.
        `field` : `str`
            MARC field to extract.
        `subfield` : `str`, optional
            MARC subfield to extract. None by default.

        Returns
        -------
        `Optional[str | Dict[str, Any]]`
            The extracted field.
        """
        try:
            result = list(
                map(
                    lambda x: x[subfield] if subfield else x.format_field(),
                    record.get_fields(field),
                )
            )

            if not collection and result:
                result = result[0]
            return result

        except Exception as e:
            if self.verbose:
                logger.error(f"Could not extract field {field} from MARC record. {e}")
            return None
