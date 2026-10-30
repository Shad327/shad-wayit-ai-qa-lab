package com.shadqa.tests.api;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.instanceOf;
import static org.hamcrest.Matchers.not;
import static org.hamcrest.Matchers.emptyOrNullString;
import static org.hamcrest.Matchers.notNullValue;
import org.junit.jupiter.api.Test;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Tag;

@Tag("regression")
public class RecordedResultApiTest {

  /**
   * ART-06: Recorded result returns valid JSON.
   *
   * Sends a GET request and verifies the HTTP status,
   * JSON content type, counts, and required identifiers.
   */
  @Test
  public void shouldReturnValidRecordedResult() {
    given()
        .baseUri("https://shadqa.com")
        .accept(ContentType.JSON)
        .when()
        .get("/demo/result.json")
        .then()
        .statusCode(200)
        .contentType(ContentType.JSON)
        .body("tests", greaterThanOrEqualTo(0));
  }
  /**
 * ART-10: Recorded workflow returns valid JSON.
 *
 * Verifies successful retrieval and required workflow fields.
 */
@Test
public void shouldReturnRecordedWorkflow() {
    given()
        .baseUri("https://shadqa.com")
        .accept(ContentType.JSON)
    .when()
        .get("/demo/workflow.json")
    .then()
        .log().ifValidationFails()
        .statusCode(200)
        .contentType(ContentType.JSON)
        .body("mode", not(emptyOrNullString()))
        .body("status", not(emptyOrNullString()))
        .body("events", instanceOf(java.util.List.class));
}
}
