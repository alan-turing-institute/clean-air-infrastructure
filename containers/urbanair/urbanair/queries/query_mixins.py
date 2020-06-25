from abc import ABC, abstractmethod
import datetime
from flask import Response, jsonify


class APIQueryMixin(ABC):
    @abstractmethod
    def query(self):
        """A database query which will be returned as a csv or json.
        If CSV: Ensure all columns are labled appropriately as these will be used as csv columns
        If JSON: Object will be serialised as is
        """
        pass

    def headers(self, query_result):
        """Get csv headers from the query result"""
        return [i["name"] for i in query_result.column_descriptions]

    def __generate_csv(self, *args, **kwargs):
        """Generate a csv file from a sqlalchemy query"""

        query = self.query(*args, **kwargs)

        headers = ",".join(self.headers(query)) + "\n"

        for i, row in enumerate(query.yield_per(1000).enable_eagerloads(False)):
            if i == 0:
                yield headers.encode("utf-8")

            str_row = []
            for r in row:
                if isinstance(r, str):
                    str_row.append(r)
                elif isinstance(r, datetime.datetime):
                    str_row.append(r.isoformat())
                else:
                    str_row.append(str(r))

            csv = ",".join(str_row) + "\n"
            yield csv.encode("utf-8")

    def stream_csv(self, filename, *args, **kwargs):
        """Stream a csv"""

        response = Response(self.__generate_csv(*args, **kwargs), mimetype="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"

        return response

    def __generate_json(self, *args, **kwargs):
        """Generate serialised json from a sqlalchemy query"""

        query = self.query(*args, **kwargs)

        return jsonify(query)

    def response_json(self, *args, **kwargs):
        """Respond with JSON"""

        return self.__generate_json(*args, **kwargs)
