package com.shadqa.tests.performance;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import io.restassured.http.ContentType;

@Tag("performance")
@Tag("regression")
@Tag("local")
public class EvidencePerformanceTest {

    /**
     * PERF-01: Record a local search response-time baseline.
     *
     * Measures five sequential requests after one warm-up.
     * Validates successful responses without imposing
     * an unagreed timing threshold.
     */
    @Test
    public void shouldMeasureSearchResponseTimes() {
        // Warm up the HTTP client and service.
        sendSearch();

        List<Long> durations = new ArrayList<>();

        for (int attempt = 1; attempt <= 5; attempt++) {
            long milliseconds = sendSearch();
            durations.add(milliseconds);

            System.out.printf(
                "Request %d: %d ms%n",
                attempt,
                milliseconds
            );
        }

        Collections.sort(durations);

        long median = durations.get(durations.size() / 2);
        long slowest = durations.get(durations.size() - 1);

        System.out.printf(
            "Median: %d ms | Slowest: %d ms%n",
            median,
            slowest
        );
    }

    private long sendSearch() {
        return given()
            .baseUri("http://127.0.0.1:8000")
            .contentType(ContentType.JSON)
            .accept(ContentType.JSON)
            .body("""
                {
                  "query": "AUTH-04",
                  "limit": 1
                }
                """)
        .when()
            .post("/retrieve")
        .then()
            .log().ifValidationFails()
            .statusCode(200)
            .contentType(ContentType.JSON)
            .body("status", equalTo("matches_found"))
            .body("results[0].id", equalTo("AUTH-04"))
            .extract()
            .response()
            .time();
    }
}
