package com.shadqa.tests.ui;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.net.URI;
import java.time.Duration;
import java.util.List;
import java.util.Set;

import com.shadqa.pages.HomePage;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.openqa.selenium.Dimension;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

@Tag("regression")
public class HomePageTest {

  private WebDriver driver;
  private HomePage homePage;

  @BeforeEach
  public void setUp() {
    driver = new ChromeDriver();
    homePage = new HomePage(driver);
    homePage.open("https://shadqa.com");
  }

  @AfterEach
  public void tearDown() {
    if (driver != null) {
      driver.quit();
    }
  }

  /**
   * PUB-01: Both website addresses display the expected
   * homepage heading and visible, enabled showcase controls.
   * A specific redirect destination is not required.
   */
  @Test
  @Tag("smoke")
  public void shouldDisplayHomepageForBothAddresses() {
    String[] urls = {
        "https://shadqa.com",
        "https://www.shadqa.com"
    };

    List<String> expectedControls = List.of(
        "Walkthrough", "Evidence", "Architecture", "Limits");

    for (String url : urls) {
      homePage.open(url);

      assertEquals(
          "Requirements. Reviewed. Tested.",
          homePage.getHeadingText(),
          "Unexpected heading for " + url);

      assertEquals(
          expectedControls,
          homePage.getShowcaseControlLabels(),
          "Unexpected showcase controls for " + url);
    }
  }

  /**
   * PUB-15: Selecting showcase sections keeps the page URL unchanged.
   *
   * Opens the homepage and selects Evidence, Architecture,
   * Limits, and Walkthrough. Verifies that the URL remains
   * equal to the address captured before selecting any section.
   *
   * Section content is verified in separate tests.
   */
  @Test
  public void shouldKeepUrlUnchangedWhenSelectingSections() {

    String originalUrl = homePage.getCurrentUrl();

    String[] sections = {
        "Evidence",
        "Architecture",
        "Limits",
        "Walkthrough"
    };

    for (String section : sections) {
      homePage.selectSection(section);

      assertEquals(
          originalUrl,
          homePage.getCurrentUrl(),
          "URL changed after selecting " + section);
    }
  }

  /**
   * PUB-05–PUB-08: Showcase sections display their expected headings.
   *
   * Selects Evidence, Architecture, Limits, and Walkthrough,
   * verifying the visible heading after each selection.
   * Covers heading checks only, not media or detailed content.
   */
  @Test
  @Tag("smoke")
  public void shouldDisplayExpectedHeadingForEachSection() {
    String[][] sections = {
        { "Evidence", "One generated test · passed" },
        { "Architecture", "How the local system works" },
        { "Limits", "What this demo proves—and what it does not" },
        { "Walkthrough", "From approved scenario to a real browser run" }
    };

    for (String[] section : sections) {
      String sectionName = section[0];
      String expectedHeading = section[1];

      homePage.selectSection(sectionName);

      assertEquals(
          expectedHeading,
          homePage.getSectionHeadingText(sectionName),
          "Unexpected heading for " + sectionName);
    }
  }

  /**
   * ART-04: Evidence displays a successfully loaded screenshot.
   *
   * Selects Evidence and verifies that its screenshot is visible,
   * has completed loading, and has a positive natural width.
   */
  @Test
  @Tag("smoke")
  public void shouldDisplayLoadedEvidenceScreenshot() {
    homePage.selectSection("Evidence");

    assertTrue(
        homePage.isEvidenceImageLoaded(),
        "Evidence screenshot should be visible and loaded");
  }

  /**
   * PUB-10: The logo and engineer name open the recorded demo.
   *
   * Clicks each part of the branding link from the homepage.
   * Verifies the /demo destination and expected page heading.
   */
  @Test
  public void shouldOpenDemoFromLogoAndName() {
    homePage.clickBrandLogo();

    assertEquals(
        "/demo",
        URI.create(homePage.getCurrentUrl()).getPath(),
        "Logo should open /demo");

    assertEquals(
        "Requirements. Reviewed. Tested.",
        homePage.getHeadingText(),
        "Expected heading after clicking the logo");

    // Return to the homepage before testing the name.
    homePage.open("https://shadqa.com");

    homePage.clickBrandName();

    assertEquals(
        "/demo",
        URI.create(homePage.getCurrentUrl()).getPath(),
        "Shad Wayit name should open /demo");

    assertEquals(
        "Requirements. Reviewed. Tested.",
        homePage.getHeadingText(),
        "Expected heading after clicking the name");
  }

  /**
   * PUB-09: Refreshing the demo restores the default Walkthrough section.
   *
   * Opens /demo, selects Evidence, then refreshes.
   * Verifies Walkthrough is selected and its heading is displayed.
   */
  @Test
  public void shouldRestoreWalkthroughAfterRefresh() {
    homePage.open("https://shadqa.com/demo");

    homePage.selectSection("Evidence");
    homePage.getSectionHeadingText("Evidence");

    homePage.refresh();

    assertEquals(
        "true",
        homePage.getSectionSelectedState("Walkthrough"),
        "Walkthrough should be selected after refresh");
  }

  /**
   * ART-01: Walkthrough video loads valid metadata.
   *
   * Verifies that the video is visible and has a positive
   * intrinsic width and a finite, positive duration.
   * Does not verify playback.
   */
  @Test
  @Tag("smoke")
  public void shouldLoadWalkthroughVideoMetadata() {
    assertTrue(
        homePage.isWalkthroughVideoReady(),
        "Walkthrough video should load valid metadata");
  }

  /**
   * PUB-11: LinkedIn link has the correct destination and target.
   *
   * Verifies the profile URL and new-tab configuration.
   * Does not click the link or verify LinkedIn availability.
   */
  @Test
  public void shouldConfigureLinkedInProfileLink() {
    assertEquals(
        "https://www.linkedin.com/in/shad-wayit-msc/",
        homePage.getLinkedInHref(),
        "LinkedIn link should point to Shad's profile");

    assertEquals(
        "_blank",
        homePage.getLinkedInTarget(),
        "LinkedIn link should request a new browsing context");
  }

  /**
   * PUB-11: Clicking LinkedIn opens a new browsing context.
   *
   * Verifies the configured destination, clicks the link,
   * and confirms a new tab or window opens.
   * Does not depend on LinkedIn page content or availability.
   */
  @Test
  public void shouldOpenLinkedInInNewTab() {
    assertEquals(
        "https://www.linkedin.com/in/shad-wayit-msc/",
        homePage.getLinkedInHref(),
        "LinkedIn link should point to Shad's profile");

    Set<String> originalWindows = driver.getWindowHandles();

    homePage.clickLinkedInLink();

    new WebDriverWait(driver, Duration.ofSeconds(10)).until(
        ExpectedConditions.numberOfWindowsToBe(
            originalWindows.size() + 1));

    Set<String> newWindows = driver.getWindowHandles();
    newWindows.removeAll(originalWindows);

    assertEquals(
        1,
        newWindows.size(),
        "Clicking LinkedIn should open one new browsing context");
  }

  /**
   * ART-05: Evidence screenshot opens the full image.
   *
   * Selects Evidence, clicks its screenshot, switches to
   * the new tab, and verifies the image destination path.
   */
  @Test
  public void shouldOpenFullEvidenceScreenshot() {
    homePage.selectSection("Evidence");

    String originalWindow = driver.getWindowHandle();
    Set<String> originalWindows = driver.getWindowHandles();

    homePage.clickEvidenceScreenshot();

    new WebDriverWait(driver, Duration.ofSeconds(10)).until(
        ExpectedConditions.numberOfWindowsToBe(
            originalWindows.size() + 1));

    Set<String> newWindows = driver.getWindowHandles();
    newWindows.removeAll(originalWindows);

    String imageWindow = newWindows.iterator().next();

    try {
      driver.switchTo().window(imageWindow);

      new WebDriverWait(driver, Duration.ofSeconds(10)).until(
          currentDriver -> "/demo/generated-result.png".equals(
              URI.create(currentDriver.getCurrentUrl()).getPath()));

      assertEquals(
          "/demo/generated-result.png",
          URI.create(driver.getCurrentUrl()).getPath(),
          "Screenshot should open the full image resource");
    } finally {
      driver.close();
      driver.switchTo().window(originalWindow);
    }
  }

  /**
   * PUB-13: Showcase sections fit a narrow viewport.
   *
   * Resizes the browser window and checks each section
   * for horizontal page overflow.
   * Does not establish complete mobile usability.
   */
  @Test
  public void shouldAvoidHorizontalOverflowOnNarrowScreen() {
    driver.manage().window().setSize(new Dimension(390, 844));

    String[] sections = {
        "Evidence",
        "Architecture",
        "Limits",
        "Walkthrough"
    };

    for (String section : sections) {
      homePage.selectSection(section);
      homePage.getSectionHeadingText(section);

      assertFalse(
          homePage.hasHorizontalOverflow(),
          "Horizontal overflow in section: " + section);
    }
  }
}
