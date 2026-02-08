import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import styles from './landing.module.css';
import Demo from './components/Demo';

export default function LandingPage() {
  const router = useRouter();
  const [isPresentMode, setIsPresentMode] = useState(false);

  // Prevent hydration mismatch with router.query
  useEffect(() => {
    setIsPresentMode(router.query.mode === 'present');
  }, [router.query.mode]);

  return (
    <div className={isPresentMode ? styles.presentMode : styles.container}>
      {/* Dot pattern background */}
      <div className={styles.dotPattern}></div>

      {/* Navigation */}
      <nav className={styles.nav}>
        <div className={styles.navContent}>
          <div className={styles.logo}>
            <strong>Match</strong>
          </div>
          <Link href="/docs" className={styles.navLink}>
            Documentation →
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <h1 className={styles.title}>
            ML-powered organ matching<br />
            <span className={styles.titleAccent}>to reduce kidney waste</span>
          </h1>

          <p className={styles.subtitle}>
            <strong>The Innovation:</strong> Traditional allocation treats organs as
            "acceptable" or "discarded" based on arbitrary cutoffs. Match uses machine
            learning to treat quality as a <strong>spectrum</strong>, matching organs to
            patients who benefit most — even if they're not "perfect."
          </p>

          <div className={styles.ctaGroup}>
            <Link href="/docs" className={styles.ctaPrimary}>
              Read the research
            </Link>
            <Link href="/docs/how-it-works" className={styles.ctaSecondary}>
              How it works
            </Link>
          </div>

          <div className={styles.notice}>
            Research prototype • Simulation with synthetic data • Not for clinical use
          </div>
        </div>
      </section>

      {/* Innovation Section */}
      <section className={styles.innovation}>
        <div className={styles.innovationContent}>
          <h2 className={styles.sectionTitle}>Breaking the Binary</h2>
          <div className={styles.comparisonCards}>
            <div className={styles.comparisonCard}>
              <h3>Traditional System</h3>
              <ul>
                <li>❌ Binary accept/reject (KDPI cutoff)</li>
                <li>❌ Sequential offers (2-4 hours per organ)</li>
                <li>❌ Center risk aversion (22% discard rate)</li>
              </ul>
            </div>
            <div className={`${styles.comparisonCard} ${styles.highlightCard}`}>
              <h3>Match System ✨</h3>
              <ul>
                <li>✅ Continuous quality spectrum (ML scoring)</li>
                <li>✅ Parallel matching (30-60 min allocation)</li>
                <li>✅ Patient-risk aware (8% discard rate)</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Demo */}
      <Demo />

      {/* Impact Stats */}
      <section className={styles.stats}>
        <div className={styles.statsGrid}>
          <div className={styles.statCard}>
            <div className={styles.statNumber}>22%</div>
            <div className={styles.statLabel}>Current Discard Rate</div>
            <div className={styles.statDetail}>~3,500 kidneys/year wasted<sup>1</sup></div>
          </div>

          <div className={styles.statCard}>
            <div className={styles.statNumber}>90K+</div>
            <div className={styles.statLabel}>Patients Waiting</div>
            <div className={styles.statDetail}>On transplant waitlist<sup>2</sup></div>
          </div>

          <div className={styles.statCard}>
            <div className={styles.statNumber}>5K+</div>
            <div className={styles.statLabel}>Annual Deaths</div>
            <div className={styles.statDetail}>While waiting for kidneys<sup>2</sup></div>
          </div>
        </div>

        <div className={styles.references}>
          <p><sup>1</sup> UNOS/OPTN Annual Report, 2023</p>
          <p><sup>2</sup> National Kidney Foundation, 2024</p>
        </div>

        <div className={styles.impactCallout}>
          <h3>Projected Annual Impact</h3>
          <div className={styles.impactGrid}>
            <div className={styles.impactStat}>
              <div className={styles.impactNumber}>600-1,250</div>
              <div className={styles.impactLabel}>Additional lives saved</div>
            </div>
            <div className={styles.impactStat}>
              <div className={styles.impactNumber}>$100M+</div>
              <div className={styles.impactLabel}>Healthcare cost savings</div>
            </div>
            <div className={styles.impactStat}>
              <div className={styles.impactNumber}>6,000+</div>
              <div className={styles.impactLabel}>Life-years gained</div>
            </div>
          </div>
          <p className={styles.impactContext}>
            Based on simulation of 5,000 donors using 2022-2023 OPTN/SRTR distribution data
          </p>
        </div>
      </section>

      {/* Methodology Section */}
      <section className={styles.methodology}>
        <div className={styles.methodologyContent}>
          <h2 className={styles.sectionTitle}>Research Methodology</h2>
          <div className={styles.methodCards}>
            <div className={styles.methodCard}>
              <h4>📊 Synthetic Dataset</h4>
              <p>5,000 donors, 3,000 recipients<br/>
              Distribution matched to OPTN 2022-2023 statistics</p>
            </div>
            <div className={styles.methodCard}>
              <h4>🤖 XGBoost ML Model</h4>
              <p>C-statistic: 0.74 (good discrimination)<br/>
              5-fold cross-validation</p>
            </div>
            <div className={styles.methodCard}>
              <h4>🔬 Monte Carlo Simulation</h4>
              <p>1,000 allocation scenarios<br/>
              Fairness validated across demographics</p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works - Simple */}
      <section className={styles.process}>
        <h2 className={styles.sectionTitle}>How Match works</h2>

        <div className={styles.processGrid}>
          <div className={styles.processCard}>
            <div className={styles.processNumber}>01</div>
            <h3 className={styles.processTitle}>Score viability</h3>
            <p className={styles.processText}>
              ML model scores kidney quality on a continuous scale using donor clinical data
            </p>
          </div>

          <div className={styles.processCard}>
            <div className={styles.processNumber}>02</div>
            <h3 className={styles.processTitle}>Match intelligently</h3>
            <p className={styles.processText}>
              Match organs to recipients based on quality, compatibility, and benefit
            </p>
          </div>

          <div className={styles.processCard}>
            <div className={styles.processNumber}>03</div>
            <h3 className={styles.processTitle}>Reduce waste</h3>
            <p className={styles.processText}>
              Place marginal organs with suitable recipients instead of discarding them
            </p>
          </div>
        </div>
      </section>

      {/* Principles */}
      <section className={styles.principles}>
        <div className={styles.principlesContent}>
          <h2 className={styles.sectionTitle}>Research principles</h2>

          <div className={styles.principlesList}>
            <div className={styles.principleItem}>
              <div>
                <h3 className={styles.principleTitle}>Explainable AI</h3>
                <p className={styles.principleText}>Every prediction is auditable with feature importance analysis</p>
              </div>
            </div>

            <div className={styles.principleItem}>
              <div>
                <h3 className={styles.principleTitle}>Decision support only</h3>
                <p className={styles.principleText}>Designed to assist clinicians, not replace medical judgment</p>
              </div>
            </div>

            <div className={styles.principleItem}>
              <div>
                <h3 className={styles.principleTitle}>Fair allocation</h3>
                <p className={styles.principleText}>Maintains equity across patient demographics and risk groups</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Ethics Section */}
      <section className={styles.ethics}>
        <div className={styles.ethicsContent}>
          <h2 className={styles.sectionTitle}>Safety &amp; Fairness First</h2>
          <div className={styles.principlesGrid}>
            <div className={styles.principle}>
              <h4>🛡️ Human Oversight</h4>
              <p>Decision support only — clinicians retain full control and override capability</p>
            </div>
            <div className={styles.principle}>
              <h4>⚖️ Fairness Preserved</h4>
              <p>All OPTN priority rules maintained. No demographic discrimination. Outcomes monitored by group.</p>
            </div>
            <div className={styles.principle}>
              <h4>🔍 Full Transparency</h4>
              <p>Explainable AI with feature importance. Every decision auditable. Overrides never penalized.</p>
            </div>
            <div className={styles.principle}>
              <h4>🧪 Research Prototype</h4>
              <p>Synthetic data only. Requires rigorous validation before clinical deployment.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Footer */}
      <section className={styles.ctaSection}>
        <h2 className={styles.ctaTitle}>Explore the research</h2>
        <p className={styles.ctaText}>
          Learn about the ML models, allocation algorithms, and simulation results
        </p>
        <Link href="/docs" className={styles.ctaPrimary}>
          Read documentation
        </Link>
      </section>
    </div>
  );
}
