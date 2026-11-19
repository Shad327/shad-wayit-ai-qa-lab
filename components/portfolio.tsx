const experience = [
  {
    company: "TELUS Digital (WillowTree)",
    role: "Software Engineer",
    dates: "2023 to August 2026",
    highlights: [
      "Shipped three customer-facing web and mobile features and delivered approximately 30 backend fixes and enhancements.",
      "Reduced integration errors from 2.5% to 1.5% with request deduplication and improved timeout handling.",
      "Built Java and Spring Boot REST APIs and Python services that cut batch processing from 10 minutes to 7.",
      "Developed responsive React and TypeScript interfaces, improved SQL query performance, and resolved production defects using logs and automated regression tests.",
    ],
  },
  {
    company: "WillowTree",
    role: "Senior Software Test Engineer",
    dates: "2021 to 2023",
    highlights: [
      "Automated API, integration, and regression tests with REST Assured, Postman, and TestNG/JUnit, contributing to a 30% increase in coverage and a 25% shorter regression cycle.",
      "Tested Dairy Queen’s online ordering and Mastercard’s enterprise expense management and transaction workflows.",
    ],
  },
  {
    company: "Teklabs",
    role: "QA Engineer",
    dates: "2020",
    highlights: ["Investigated backend defects and used SQL to identify 10 critical data integrity issues for enterprise clients."],
  },
];

const skills = [
  ["Backend and data", "Java, Spring Boot, Python, REST APIs, SQL"],
  ["Frontend", "React, TypeScript, JavaScript"],
  ["Quality engineering", "Playwright, pytest, REST Assured, Postman, TestNG, JUnit"],
  ["Delivery", "Git, GitHub, Maven, Azure DevOps, CI/CD"],
];

export function Portfolio() {
  return (
    <div className="site-shell portfolio">
      <header className="topbar">
        <a className="identity" href="/"><span className="monogram" aria-hidden="true">SW</span><span>Shadman Wayit, MSc<small>Software Engineer</small></span></a>
        <nav aria-label="Portfolio">
          <a href="#experience">Experience</a>
          <a href="#projects">Projects</a>
          <a href="https://www.linkedin.com/in/shad-wayit-msc/">LinkedIn</a>
        </nav>
      </header>
      <main>
        <section className="portfolio-hero" aria-labelledby="portfolio-name">
          <p className="eyebrow">SOFTWARE ENGINEER</p>
          <h1 id="portfolio-name">Shadman Wayit, <span>MSc</span></h1>
          <p className="intro-copy">I build full-stack web and mobile applications, with a focus on Java, Spring Boot, Python, APIs, and databases. My quality engineering background spans enterprise web, mobile, and backend services.</p>
          <a className="portfolio-action" href="#projects">View my work</a>
        </section>

        <section className="portfolio-section" id="projects">
          <h2>Featured project</h2>
          <article className="portfolio-project">
            <h3>AI QA Lab</h3>
            <p>I built a React workspace that connects product requirements, evidence review, and browser test results. The Python, pytest, and Playwright pipeline records local runs and links test evidence back to its source requirements.</p>
            <a href="/demo">Watch the recorded NoiseLabz walkthrough</a>
          </article>
        </section>

        <section className="portfolio-section" id="experience">
          <h2>Experience</h2>
          {experience.map(({ company, role, dates, highlights }) => (
            <article className="portfolio-role" key={role}>
              <div>
                <h3>{role}</h3>
                <p>{company}</p>
                <p>{dates}</p>
              </div>
              <ul>{highlights.map(highlight => <li key={highlight}>{highlight}</li>)}</ul>
            </article>
          ))}
        </section>

        <div className="portfolio-details">
          <section className="portfolio-section">
            <h2>Technical skills</h2>
            <dl>
              {skills.map(([area, tools]) => <div key={area}><dt>{area}</dt><dd>{tools}</dd></div>)}
            </dl>
          </section>
          <section className="portfolio-section">
            <h2>Education and certifications</h2>
            <dl>
              <div><dt>Master of Science</dt><dd>SUNY Oswego</dd></div>
              <div><dt>Certifications</dt><dd>ISTQB Certified Software Tester<br />Google Cybersecurity Certificate</dd></div>
            </dl>
          </section>
        </div>
      </main>
      <footer><span>Shadman Wayit, MSc · Fort Smith, Arkansas</span></footer>
    </div>
  );
}
