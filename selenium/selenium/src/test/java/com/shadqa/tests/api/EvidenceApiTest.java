package com.shadqa.tests.api;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.greaterThan;
import static org.hamcrest.Matchers.hasItem;

import java.util.Map;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import io.restassured.http.ContentType;

@Tag("regression")
@Tag("local")
public class EvidenceApiTest {

  /**
   * API-02a: A valid query returns matching requirement evidence.
   *
   * Requires the local API running with api-test-requirements.md.
   */
  @Test
  public void shouldReturnEvidenceForValidQuery() {
    given()
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
        .body("query", equalTo("AUTH-04"))
        .body("status", equalTo("matches_found"))
        .body("results", hasSize(1))
        .body("results[0].id", equalTo("AUTH-04"))
        .body(
            "results[0].text",
            equalTo("**AUTH-04** Browse without a wallet."));
  }
  /**
 * API-02b: A blank query is rejected with a validation error.
 *
 * Sends whitespace instead of a meaningful search query.
 * Verifies HTTP 422 and an error identifying the query field.
 */
@Test
public void shouldRejectBlankQuery() {
    given()
        .baseUri("http://127.0.0.1:8000")
        .contentType(ContentType.JSON)
        .accept(ContentType.JSON)
        .body("""
            {
              "query": "   ",
              "limit": 1
            }
            """)
    .when()
        .post("/retrieve")
    .then()
        .log().ifValidationFails()
        .statusCode(422)
        .contentType(ContentType.JSON)
        .body("detail.size()", greaterThan(0))
        .body("detail[0].loc", hasItem("query"));
}
/**
 * API-02c: A search limit above 10 is rejected.
 *
 * Sends a valid query with limit 11.
 * Verifies HTTP 422 and an error identifying the limit field.
 */
@Test
public void shouldRejectLimitAboveMaximum() {
    given()
        .baseUri("http://127.0.0.1:8000")
        .contentType(ContentType.JSON)
        .accept(ContentType.JSON)
        .body("""
            {
              "query": "AUTH-04",
              "limit": 11
            }
            """)
    .when()
        .post("/retrieve")
    .then()
        .log().ifValidationFails()
        .statusCode(422)
        .contentType(ContentType.JSON)
        .body("detail.size()", greaterThan(0))
        .body("detail[0].loc", hasItem("limit"));
}
/**
 * API-02d: An unmatched query returns an empty search result.
 *
 * Searches for AUTH-99, which is absent from our practice fixture.
 * Verifies successful processing without invented evidence.
 */
@Test
public void shouldReturnNoEvidenceForUnmatchedQuery() {
    given()
        .baseUri("http://127.0.0.1:8000")
        .contentType(ContentType.JSON)
        .accept(ContentType.JSON)
        .body("""
            {
              "query": "AUTH-99",
              "limit": 1
            }
            """)
    .when()
        .post("/retrieve")
    .then()
        .log().ifValidationFails()
        .statusCode(200)
        .contentType(ContentType.JSON)
        .body("query", equalTo("AUTH-99"))
        .body("status", equalTo("no_evidence"))
        .body("results", hasSize(0));
}
/**
 * API-02e: A request without the required query is rejected.
 *
 * Sends only limit and verifies HTTP 422,
 * identifying query as the missing field.
 */
@Test
public void shouldRejectMissingQuery() {
    given()
        .baseUri("http://127.0.0.1:8000")
        .contentType(ContentType.JSON)
        .accept(ContentType.JSON)
        .body("""
            {
              "limit": 1
            }
            """)
    .when()
        .post("/retrieve")
    .then()
        .log().ifValidationFails()
        .statusCode(422)
        .contentType(ContentType.JSON)
        .body("detail.size()", greaterThan(0))
        .body("detail[0].loc", hasItem("query"))
        .body("detail[0].type", equalTo("missing"));
}
/**
 * API-SEC-01: Callers cannot supply a requirements source path.
 *
 * Sends an unexpected source field and verifies
 * that request validation rejects it.
 */
@Test
public void shouldRejectCallerSuppliedSource() {
    given()
        .baseUri("http://127.0.0.1:8000")
        .contentType(ContentType.JSON)
        .accept(ContentType.JSON)
        .body("""
            {
              "query": "AUTH-04",
              "limit": 1,
              "source": "another-file.md"
            }
            """)
    .when()
        .post("/retrieve")
    .then()
        .log().ifValidationFails()
        .statusCode(422)
        .contentType(ContentType.JSON)
        .body("detail[0].loc", hasItem("source"))
        .body("detail[0].type", equalTo("extra_forbidden"));
}
}
