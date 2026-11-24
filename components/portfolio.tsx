const experience = [
  {
    company: "TELUS Digital (WillowTree)",
    role: "Software Engineer",
    dates: "2023 to August 2026",
    highlights: [
      "Engineered and shipped 3 customer-facing features for web and mobile applications by translating product requirements into reusable components and backend services.",
      "Reduced batch processing time by 30% (from 10 to 7 minutes) by creating Java/Spring Boot REST APIs and Python services for workflow automation.",
      "Developed responsive React/TypeScript interfaces, reducing UI defects by 25% (from 20 to 15 per release) via accessibility, validation, and API integration.",
      "Diagnosed and resolved production defects, reducing critical bugs by 30% (from 10 to 7 per quarter) through log analysis, debugging, and automated regression tests.",
      "Optimized SQL queries and database access, achieving a 30% improvement in application performance and data retrieval.",
      "Executed in code reviews, technical design discussions, and CI/CD workflows to deliver maintainable software.",
      "Identified and resolved 25+ critical bugs by utilizing AI assistants for comprehensive tracing and analysis, ensuring robust code fixes and system integrity.",
    ],
  },
  {
    company: "WillowTree",
    role: "Senior Software Test Engineer",
    dates: "2021 to 2023",
    highlights: [
      "Automated API, integration, and regression tests using REST Assured, Postman, and TestNG/JUnit within CI/CD workflows, contributing to a 30% coverage increase and a 25% reduction in regression cycle time.",
      "Executed functional, UI, and regression testing for Dairy Queen's online ordering, decreasing defect re-open rate by 15%.",
      "Managed and performed functional, integration, API, and end-to-end testing for Mastercard's expense management and transaction workflows, supporting 3 enterprise clients.",
    ],
  },
  {
    company: "Teklabs",
    role: "QA Engineer",
    dates: "2020",
    highlights: [
      "Investigated backend defects and identified data integrity using SQL queries, identifying 10 critical issues for enterprise clients.",
    ],
  },
];

const skills = [
  ["Languages and frontend", "Java, TypeScript, JavaScript, SQL, React, HTML, CSS"],
  [
    "Developer tools and practices",
    "Git, GitHub, Maven, Azure DevOps, CI/CD, Debugging, Root CauseAnalysis, Automated Testing, Agile/Scrum",
  ],
  ["Backend and APIs ", "REST APIs, API Integration, Microservices Testing, SQL Queries"],
  ["Portfolio tools", "Python, pytest, Playwright"],
];

export function Portfolio() {
  return (
    <div className="site-shell portfolio">
      <header className="topbar">
        <a className="identity" href="/">
          <img src="/profile.png" alt="" width={44} height={44} className="rounded-full object-cover" />
          <span>
            Shadman Wayit, MSc<small>Software Engineer</small>
          </span>
        </a>
        <nav aria-label="Portfolio">
          <a href="#experience">Experience</a>
          <a href="#projects">Projects</a>
          <a href="https://www.linkedin.com/in/shad-wayit-msc/">LinkedIn</a>
        </nav>
      </header>
      <main>
        <section className="portfolio-hero" aria-labelledby="portfolio-name">
          <p className="eyebrow">SOFTWARE ENGINEER</p>
          <h1 id="portfolio-name">
            Shadman Wayit, <span>MSc</span>
          </h1>
          <p className="intro-copy">
            Software Engineer with experience building full-stack web and mobile applications, with a focus on
            Java, Spring Boot, Python, APIs, and database work.
          </p>
          <ul className="portfolio-summary">
            <li>
              Reduced integration errors by <strong>40%</strong>, from 2.5% to 1.5%, by implementing request
              deduplication and improving timeout handling.
            </li>
            <li>
              Delivered approximately <strong>30 backend fixes and enhancements</strong> over nearly three
              years at TELUS Digital.
            </li>
            <li>
              Led quality engineering for enterprise applications, covering system, integration, and
              regression testing across web, mobile, and backend services.
            </li>
          </ul>
          <a className="portfolio-action" href="#projects">
            View my work
          </a>
        </section>

        <section className="portfolio-section" id="projects">
          <h2>Featured project</h2>
          <article className="portfolio-project">
            <h3>AI QA Lab</h3>
            <p>
              I built a React workspace that connects product requirements, evidence review, and browser test
              results. The Python, pytest, and Playwright pipeline records local runs and links test evidence
              back to its source requirements.
            </p>
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
              <ul>
                {highlights.map((highlight) => (
                  <li key={highlight}>{highlight}</li>
                ))}
              </ul>
            </article>
          ))}
        </section>

        <div className="portfolio-details">
          <section className="portfolio-section">
            <h2>Technical skills</h2>
            <dl>
              {skills.map(([area, tools]) => (
                <div key={area}>
                  <dt>{area}</dt>
                  <dd>{tools}</dd>
                </div>
              ))}
            </dl>
          </section>
          <section className="portfolio-section">
            <h2>Education and certifications</h2>
            <dl>
              <div>
                <dt>Master of Science</dt>
                <dd>SUNY Oswego</dd>
              </div>
              <div>
                <dt>Certifications</dt>
                <dd>
                  ISTQB Certified Software Tester
                  <br />
                  Google Cybersecurity Certificate
                </dd>
              </div>
            </dl>
          </section>
        </div>
      </main>
      <footer>
        <span>Shadman Wayit, MSc · Fort Smith, Arkansas</span>
      </footer>
    </div>
  );
}
