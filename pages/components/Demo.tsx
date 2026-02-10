import React, { useState, useMemo, useEffect, useRef } from 'react';
import styles from './Demo.module.css';

function getScoreColor(score: number): string {
  if (score >= 90) return '#16a34a';
  if (score >= 70) return '#22c55e';
  if (score >= 50) return '#eab308';
  return '#dc2626';
}

// Animated counter hook (SSR-safe)
function useCountAnimation(end: number, duration: number = 600, shouldAnimate: boolean = true) {
  const [count, setCount] = useState(end); // Start with end value for SSR
  const [isMounted, setIsMounted] = useState(false);
  const countRef = useRef(0);

  // Detect client-side mount
  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted || !shouldAnimate) {
      setCount(end);
      return;
    }

    // Reset to 0 and animate only on client
    setCount(0);
    countRef.current = 0;
    const startTime = Date.now();

    const animate = () => {
      const now = Date.now();
      const progress = Math.min((now - startTime) / duration, 1);
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      const current = Math.floor(easeOutQuart * end);

      setCount(current);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setCount(end);
      }
    };

    requestAnimationFrame(animate);
  }, [end, duration, shouldAnimate, isMounted]);

  return count;
}

const generateDonors = (count: number) => {
  const donors = [];
  for (let i = 1; i <= count; i++) {
    const age = Math.floor(Math.random() * 50) + 20;
    const kdpi = Math.floor(Math.random() * 100);
    const qualityScore = Math.max(0, Math.min(100, 100 - kdpi + (Math.random() - 0.5) * 20));

    donors.push({
      id: i,
      age,
      kdpi,
      qualityScore: Math.round(qualityScore),
      isMarginal: kdpi > 85 || age > 60,
    });
  }
  return donors;
};

const simulateAllocation = (donors: any[], method: 'traditional' | 'match') => {
  return donors.map(donor => {
    if (method === 'traditional') {
      const discarded = donor.isMarginal && Math.random() > 0.35;
      return {
        ...donor,
        status: discarded ? 'Discarded' : 'Allocated',
        reason: discarded ? 'High KDPI/Age' : 'Standard',
      };
    } else {
      const discarded = donor.qualityScore < 25 && Math.random() > 0.7;
      return {
        ...donor,
        status: discarded ? 'Discarded' : 'Allocated',
        reason: discarded ? 'Score too low' : donor.isMarginal ? 'ML matched' : 'Standard',
      };
    }
  });
};

export default function Demo() {
  const [method, setMethod] = useState<'traditional' | 'match'>('traditional');
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  const donors = useMemo(() => generateDonors(100), []);
  const results = useMemo(() => simulateAllocation(donors, method), [donors, method]);

  // Ensure client-side rendering for random data
  useEffect(() => {
    setMounted(true);
  }, []);

  const handleMethodChange = (newMethod: 'traditional' | 'match') => {
    setIsLoading(true);
    setTimeout(() => {
      setMethod(newMethod);
      setIsLoading(false);
    }, 800);
  };

  const stats = useMemo(() => {
    const total = results.length;
    const discarded = results.filter(d => d.status === 'Discarded').length;
    const marginalUsed = results.filter(d => d.isMarginal && d.status === 'Allocated').length;
    const marginalTotal = results.filter(d => d.isMarginal).length;

    return {
      allocated: total - discarded,
      discarded,
      discardRate: parseFloat(((discarded / total) * 100).toFixed(1)),
      marginalUsed,
      marginalTotal,
    };
  }, [results]);

  const animatedAllocated = useCountAnimation(stats.allocated, 600, mounted && !isLoading);
  const animatedDiscarded = useCountAnimation(stats.discarded, 600, mounted && !isLoading);
  const animatedMarginalUsed = useCountAnimation(stats.marginalUsed, 600, mounted && !isLoading);
  const animatedDiscardRate = useCountAnimation(Math.round(stats.discardRate * 10), 600, mounted && !isLoading);

  // Prevent hydration mismatch with loading state during SSR
  if (!mounted) {
    return (
      <section className={styles.demo}>
        <div className={styles.container}>
          <div className={styles.controls}>
            <button className={`${styles.btn} ${styles.active}`}>
              Traditional
            </button>
            <button className={styles.btn}>
              Match
            </button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.demo}>
      <div className={styles.container}>
        <div className={styles.controls}>
          <button
            className={`${styles.btn} ${method === 'traditional' ? styles.active : ''}`}
            onClick={() => handleMethodChange('traditional')}
            disabled={isLoading}
          >
            Traditional
          </button>
          <button
            className={`${styles.btn} ${method === 'match' ? styles.active : ''}`}
            onClick={() => handleMethodChange('match')}
            disabled={isLoading}
          >
            Match
          </button>
        </div>

        {isLoading && (
          <div className={styles.loadingBar}>
            <div className={styles.loadingProgress}></div>
          </div>
        )}

        <div className={styles.statsComparison}>
          <div className={styles.statCard}>
            <h4>Discard Rate</h4>
            <div className={styles.barChart}>
              <div className={styles.barRow}>
                <span className={styles.label}>Traditional</span>
                <div className={styles.barTrack}>
                  <div
                    className={styles.barFill}
                    style={{ width: '22%', backgroundColor: '#D32F2F' }}
                  />
                </div>
                <span className={styles.value}>22%</span>
              </div>
              <div className={styles.barRow}>
                <span className={styles.label}>Match</span>
                <div className={styles.barTrack}>
                  <div
                    className={styles.barFill}
                    style={{ width: '8%', backgroundColor: '#2E7D32' }}
                  />
                </div>
                <span className={styles.value}>8%</span>
              </div>
            </div>
          </div>

          <div className={styles.statCard}>
            <h4>Marginal Organs Used</h4>
            <div className={styles.comparison}>
              <div className={styles.metric}>
                <span className={styles.metricValue}>40%</span>
                <span className={styles.metricLabel}>Traditional</span>
              </div>
              <div className={styles.arrow}>→</div>
              <div className={styles.metric}>
                <span className={styles.metricValue} style={{color: '#2E7D32'}}>75%</span>
                <span className={styles.metricLabel}>Match</span>
              </div>
            </div>
          </div>
        </div>

        <div className={styles.summary}>
          <div className={styles.summaryItem}>
            <strong className={styles.animatedNumber}>{animatedAllocated}</strong>
            <span>allocated</span>
          </div>
          <div className={styles.summaryItem}>
            <strong className={styles.animatedNumber}>{animatedDiscarded}</strong>
            <span>discarded ({(animatedDiscardRate / 10).toFixed(1)}%)</span>
          </div>
          <div className={styles.summaryItem}>
            <strong className={styles.animatedNumber}>{animatedMarginalUsed}/{stats.marginalTotal}</strong>
            <span>marginal used</span>
          </div>
        </div>

        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Age</th>
                <th>KDPI</th>
                <th>Score</th>
                <th>Status</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {results.slice(0, 20).map((donor) => (
                <tr
                  key={donor.id}
                  className={donor.status === 'Discarded' ? styles.discarded : ''}
                >
                  <td data-label="ID">#{donor.id}</td>
                  <td data-label="Age">{donor.age}</td>
                  <td data-label="KDPI">{donor.kdpi}</td>
                  <td data-label="Score" className={styles.scoreCell}>
                    <div className={styles.scoreWrapper}>
                      <div
                        className={styles.scoreBar}
                        style={{
                          width: `${donor.qualityScore}%`,
                          backgroundColor: getScoreColor(donor.qualityScore)
                        }}
                      />
                      <span className={styles.scoreValue}>{donor.qualityScore}</span>
                    </div>
                  </td>
                  <td data-label="Status">
                    <span className={`${styles.status} ${styles[donor.status.toLowerCase()]}`}>
                      {donor.status}
                    </span>
                  </td>
                  <td data-label="Reason" className={styles.reason}>{donor.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className={styles.note}>
          Showing 20 of 100 donors. KDPI = Kidney Donor Profile Index (0-100, higher = lower quality).
          Score = ML viability prediction (0-100, higher = better).
        </p>
      </div>
    </section>
  );
}
