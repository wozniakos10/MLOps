DROP TABLE IF EXISTS disruptions;
CREATE TABLE disruptions (
    "rdt_id" INT,
    "ns_lines" TEXT,
    "rdt_lines" TEXT,
    "rdt_lines_id" TEXT,
    "rdt_station_names" TEXT,
    "rdt_station_codes" TEXT,
    "cause_nl" TEXT,
    "cause_en" TEXT,
    "statistical_cause_nl" TEXT,
    "statistical_cause_en" TEXT,
    "cause_group" TEXT,
    "start_time" TIMESTAMP,
    "end_time" TIMESTAMP,
    "duration_minutes" INT
);


