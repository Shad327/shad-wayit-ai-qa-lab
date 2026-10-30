package com.shadqa.pages;

import java.time.Duration;
import java.util.List;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.JavascriptExecutor;

public class HomePage {

  private static final By HEADING = By.xpath("//main//h1");

  private static final By SHOWCASE_CONTROLS = By.xpath(
      "//div[@role='group' and @aria-label='Showcase sections']//button");

  private By sectionButton(String sectionName) {
    return By.xpath(
        "//div[@role='group' and @aria-label='Showcase sections']"
            + "//button[normalize-space(.)='" + sectionName + "']");
  }

  public void selectSection(String sectionName) {
    wait.until(
        ExpectedConditions.elementToBeClickable(
            sectionButton(sectionName)))
        .click();
  }

  public void refresh() {
    driver.navigate().refresh();

    wait.until(
        ExpectedConditions.elementToBeClickable(SHOWCASE_CONTROLS));
  }

  public String getSectionSelectedState(String sectionName) {
    return wait.until(
        ExpectedConditions.visibilityOfElementLocated(
            sectionButton(sectionName)))
        .getDomAttribute("aria-pressed");
  }

  private static final By EVIDENCE_IMAGE = By.xpath(
      "//img[@alt='Final Roadmap section after the generated navigation test']");
  private final WebDriver driver;
  private final WebDriverWait wait;

  public HomePage(WebDriver driver) {
    this.driver = driver;
    this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
  }

  public String getCurrentUrl() {
    return driver.getCurrentUrl();
  }

  public void open(String url) {
    driver.get(url);

    wait.until(
        ExpectedConditions.elementToBeClickable(SHOWCASE_CONTROLS));
  }

  public String getHeadingText() {
    return driver.findElement(HEADING)
        .getText()
        .replaceAll("\\s+", " ")
        .trim();
  }

  private static final By BRAND_LOGO = By.xpath(
      "//header//a[@href='/demo']//span[normalize-space(.)='SW']");

  private static final By BRAND_NAME = By.xpath(
      "//header//a[@href='/demo']//span"
          + "[text()[normalize-space(.)='Shad Wayit']]");

  public void clickBrandLogo() {
    wait.until(
        ExpectedConditions.elementToBeClickable(BRAND_LOGO)).click();

    wait.until(ExpectedConditions.urlContains("/demo"));
  }

  public void clickBrandName() {
    wait.until(
        ExpectedConditions.elementToBeClickable(BRAND_NAME)).click();

    wait.until(ExpectedConditions.urlContains("/demo"));
  }

  public List<String> getShowcaseControlLabels() {
    List<WebElement> controls = wait.until(currentDriver -> {
      List<WebElement> elements = currentDriver.findElements(SHOWCASE_CONTROLS);

      if (elements.size() != 4) {
        return null;
      }

      for (WebElement element : elements) {
        if (!element.isDisplayed() || !element.isEnabled()) {
          return null;
        }
      }

      return elements;
    });

    return controls.stream()
        .map(element -> element.getText().trim())
        .toList();
  }

  public String getSectionHeadingText(String sectionName) {
    By selectedButton = sectionButton(sectionName);
    wait.until(
        ExpectedConditions.attributeToBe(
            selectedButton, "aria-pressed", "true"));

    By heading = By.xpath(
        "//div[contains(concat(' ', normalize-space(@class), ' '),"
            + " ' showcase-content ')]//h3");

    return wait.until(
        ExpectedConditions.visibilityOfElementLocated(heading)).getText().trim();
  }

  public boolean isEvidenceImageLoaded() {
    return wait.until(currentDriver -> {
      WebElement image = currentDriver.findElement(EVIDENCE_IMAGE);

      return image.isDisplayed()
          && "true".equals(image.getDomProperty("complete"))
          && Integer.parseInt(
              image.getDomProperty("naturalWidth")) > 0;
    });
  }

  private static final By WALKTHROUGH_VIDEO = By.xpath(
      "//video[@aria-label='Recorded local QA workflow']");

  public boolean isWalkthroughVideoReady() {
    return wait.until(currentDriver -> {
      WebElement video = currentDriver.findElement(WALKTHROUGH_VIDEO);

      String readyState = video.getDomProperty("readyState");
      String width = video.getDomProperty("videoWidth");
      String duration = video.getDomProperty("duration");

      if (readyState == null || width == null || duration == null) {
        return false;
      }

      if (Integer.parseInt(readyState) < 1) {
        return false;
      }

      double durationSeconds = Double.parseDouble(duration);

      return video.isDisplayed()
          && Integer.parseInt(width) > 0
          && Double.isFinite(durationSeconds)
          && durationSeconds > 0;
    });
  }

  private static final By LINKEDIN_LINK = By.xpath(
      "//header//a[normalize-space(.)='Connect on LinkedIn']");

  public String getLinkedInHref() {
    return wait.until(
        ExpectedConditions.visibilityOfElementLocated(LINKEDIN_LINK)).getDomAttribute("href");
  }

  public String getLinkedInTarget() {
    return driver.findElement(LINKEDIN_LINK)
        .getDomAttribute("target");
  }

  public void clickLinkedInLink() {
    wait.until(
        ExpectedConditions.elementToBeClickable(LINKEDIN_LINK)).click();
  }

  public void clickEvidenceScreenshot() {
    wait.until(
        ExpectedConditions.elementToBeClickable(EVIDENCE_IMAGE)).click();
  }



public boolean hasHorizontalOverflow() {
    JavascriptExecutor js = (JavascriptExecutor) driver;

    return (Boolean) js.executeScript(
        "return document.documentElement.scrollWidth > window.innerWidth;"
    );
}
}
