'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  MapPin,
  Clock,
  DollarSign,
  Star,
  Navigation,
  CheckCircle2,
  Loader2,
  Sparkles,
  Shield,
  AlertCircle,
  ChevronRight,
  Stethoscope,
  Building2,
  CreditCard,
  ExternalLink,
  AlertTriangle,
  Info
} from 'lucide-react';

// Types matching backend response
interface RecommendedFacility {
  name: string;
  your_cost: number;
  distance_miles: number;
  wait_time: string;
  address?: string;
  rating?: number;
  url?: string;
  data_source?: string;
  confidence?: string;
}

interface Alternative {
  name: string;
  your_cost: number;
  distance_miles: number;
  wait_time: string;
  url?: string;
  data_source?: string;
}

interface Phase {
  status: string;
  duration_ms: number;
  [key: string]: unknown;
}

interface BackendResponse {
  success: boolean;
  recommended?: RecommendedFacility;
  reasoning?: string[];
  why_not_er?: string;
  alternatives?: Alternative[];
  urgency?: 'low' | 'moderate' | 'high' | 'emergency';
  care_level?: string;
  expected_procedures?: string[];
  data_quality?: string;
  disclaimer?: string;
  processing_time_ms?: number;
  phases?: Record<string, Phase>;
  error?: string;
}

// Insurance plans
const INSURANCE_PLANS = [
  { value: 'anthem_ppo', label: 'Anthem PPO' },
  { value: 'bcbs_hmo', label: 'Blue Shield HMO' },
  { value: 'aetna_ppo', label: 'Aetna PPO' },
  { value: 'kaiser', label: 'Kaiser Permanente' },
  { value: 'medicare', label: 'Medicare' },
  { value: 'uninsured', label: 'Uninsured (Cash Pay)' },
];

const urgencyLabels: Record<string, string> = {
  low: 'Low Urgency',
  moderate: 'Moderate Urgency',
  high: 'High Urgency',
  emergency: 'EMERGENCY'
};

const careLevelLabels: Record<string, string> = {
  primary_care: 'Primary Care',
  urgent_care: 'Urgent Care',
  emergency_room: 'Emergency Room',
  virtual_care: 'Virtual Care'
};

export default function Home() {
  const [symptoms, setSymptoms] = useState('');
  const [location, setLocation] = useState('San Francisco, CA');
  const [insurance, setInsurance] = useState('anthem_ppo');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BackendResponse | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const steps = [
    { label: 'Analyzing symptoms', icon: Stethoscope },
    { label: 'Searching facilities', icon: Building2 },
    { label: 'Calculating costs', icon: DollarSign },
    { label: 'Generating recommendation', icon: Sparkles }
  ];

  // Get backend URL - use env var or default to localhost
  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symptoms.trim()) return;

    setLoading(true);
    setResult(null);
    setError(null);
    setCurrentStep(0);

    // Simulate step progression for loading state
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev >= steps.length - 1) {
          return prev;
        }
        return prev + 1;
      });
    }, 1500);

    try {
      // Call the backend API directly
      const response = await fetch(`${BACKEND_URL}/advisor/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symptoms: symptoms.trim(),
          location: location.trim() || 'San Francisco, CA',
          insurance_plan: insurance === 'uninsured' ? null : insurance,
          // Include insurance object for legacy format compatibility
          insurance: insurance === 'uninsured' ? null : {
            provider: INSURANCE_PLANS.find(p => p.value === insurance)?.label || 'Unknown',
            plan_name: insurance.includes('ppo') ? 'PPO' : insurance.includes('hmo') ? 'HMO' : 'Standard'
          }
        })
      });

      const data: BackendResponse = await response.json();

      // Set all steps to complete
      setCurrentStep(steps.length);

      if (!data.success) {
        setError(data.error || 'Failed to get recommendation');
      } else {
        setResult(data);
      }
    } catch (err) {
      console.error('Error getting recommendation:', err);
      setError('Failed to connect to backend. Make sure the server is running on port 8000.');
    } finally {
      clearInterval(stepInterval);
      setLoading(false);
    }
  };

  // Calculate savings vs ER (estimate)
  const getSavingsVsER = () => {
    if (!result?.recommended) return 0;
    const erCost = 850; // Average ER visit
    return Math.max(0, erCost - (result.recommended.your_cost || 0));
  };

  // Helper to get price class
  const getPriceClass = (cost: number) => {
    if (cost > 500) return 'high';
    if (cost > 200) return 'medium';
    return 'low';
  };

  return (
    <main className="page-main">
      <div className="container">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="hero-section"
        >
          <div className="hero-badge">
            <Sparkles size={16} className="icon-primary" />
            <span className="hero-badge-text">AI-Powered Healthcare Navigator</span>
          </div>

          <h1 className="hero-title">
            <span className="text-gradient">ClearBill</span>
            <span style={{ color: 'white' }}> Advisor</span>
          </h1>

          <p className="hero-subtitle">
            Find the right care at the right price. We analyze your symptoms and insurance
            to recommend the best, most affordable care option.
          </p>
        </motion.div>

        {/* Search Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="glass-card form-card"
        >
          <form onSubmit={handleSubmit}>
            {/* Symptoms Textarea */}
            <div className="form-group">
              <label className="label">What symptoms are you experiencing?</label>
              <div className="input-wrapper">
                <Search size={20} className="input-icon-top" />
                <textarea
                  className="input input-dark textarea-symptoms"
                  placeholder="Describe your symptoms (e.g., Twisted ankle while running, swelling and pain, can't walk properly...)"
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  rows={3}
                />
              </div>
            </div>

            {/* Location and Insurance Row */}
            <div className="form-row">
              {/* Location Input */}
              <div>
                <label className="label">Your location</label>
                <div className="input-wrapper">
                  <MapPin size={20} className="input-icon" />
                  <input
                    type="text"
                    className="input input-dark input-with-icon"
                    placeholder="San Francisco, CA"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                  />
                </div>
              </div>

              {/* Insurance Dropdown */}
              <div>
                <label className="label">Your insurance plan</label>
                <div className="input-wrapper">
                  <CreditCard size={20} className="input-icon" />
                  <select
                    className="input input-dark select-styled"
                    value={insurance}
                    onChange={(e) => setInsurance(e.target.value)}
                  >
                    {INSURANCE_PLANS.map(plan => (
                      <option key={plan.value} value={plan.value}>
                        {plan.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="btn btn-primary btn-fullwidth"
              disabled={loading || !symptoms.trim()}
            >
              {loading ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  <span>Finding your best option...</span>
                </>
              ) : (
                <>
                  <Sparkles size={20} />
                  <span>Get Personalized Recommendation</span>
                </>
              )}
            </button>
          </form>
        </motion.div>

        {/* Loading State */}
        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="glass-card loading-card"
            >
              <div className="loading-steps">
                {steps.map((step, index) => {
                  const Icon = step.icon;
                  const isActive = index === currentStep;
                  const isComplete = index < currentStep;

                  return (
                    <motion.div
                      key={step.label}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`loading-step ${isActive ? 'active' : ''}`}
                    >
                      <div className={`loading-step-icon ${isComplete ? 'complete' : isActive ? 'active' : 'pending'}`}>
                        {isComplete ? (
                          <CheckCircle2 size={20} color="white" />
                        ) : isActive ? (
                          <Loader2 size={20} color="white" className="animate-spin" />
                        ) : (
                          <Icon size={20} className="icon-muted" />
                        )}
                      </div>
                      <span className={`loading-step-label ${isComplete ? 'complete' : isActive ? 'active' : ''}`}>
                        {step.label}
                      </span>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error State */}
        <AnimatePresence>
          {error && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="error-card"
            >
              <AlertTriangle size={24} className="error-icon" />
              <div>
                <h3 className="error-title">Error Getting Recommendation</h3>
                <p className="error-message">{error}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {result && !loading && result.success && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="results-container"
            >
              {/* Urgency Banner */}
              {result.urgency && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.1 }}
                  className={`urgency-banner ${result.urgency}`}
                >
                  <AlertCircle size={20} className={`urgency-label ${result.urgency}`} />
                  <div>
                    <span className={`urgency-label ${result.urgency}`}>
                      {urgencyLabels[result.urgency] || 'Moderate Urgency'}:
                    </span>
                    <span className="urgency-description">
                      {result.care_level && careLevelLabels[result.care_level]
                        ? `${careLevelLabels[result.care_level]} is recommended.`
                        : 'Please seek appropriate care.'}
                      {result.expected_procedures && result.expected_procedures.length > 0 && (
                        <span className="urgency-procedures">
                          {' '}Expected procedures: {result.expected_procedures.join(', ')}.
                        </span>
                      )}
                    </span>
                  </div>
                </motion.div>
              )}

              {/* Main Recommendation Card */}
              {result.recommended && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="recommendation-card"
                >
                  <div className="recommendation-header">
                    <Sparkles size={16} className="icon-primary" />
                    <span className="recommendation-label">Best Match for You</span>
                    {result.data_quality && (
                      <span className={`data-quality-badge ${result.data_quality === 'live' ? 'live' : 'estimated'}`}>
                        {result.data_quality === 'live' ? '● Live Data' : '● Estimated'}
                      </span>
                    )}
                  </div>

                  <div className="recommendation-content">
                    <div>
                      <h2 className="facility-name">{result.recommended.name}</h2>

                      <div className="facility-meta">
                        {result.recommended.rating && (
                          <div className="meta-item">
                            <Star size={16} fill="#fbbf24" className="icon-star" />
                            <span className="rating-text">{result.recommended.rating}</span>
                          </div>
                        )}
                        {result.recommended.distance_miles != null && (
                          <div className="meta-item">
                            <MapPin size={16} className="icon-muted" />
                            <span className="meta-item-text">{typeof result.recommended.distance_miles === 'number' ? result.recommended.distance_miles.toFixed(1) : result.recommended.distance_miles} miles</span>
                          </div>
                        )}
                        {result.recommended.wait_time && (
                          <div className="meta-item">
                            <Clock size={16} className="icon-muted" />
                            <span className="meta-item-text">{result.recommended.wait_time}</span>
                          </div>
                        )}
                      </div>

                      {result.recommended.address && (
                        <p className="facility-address">{result.recommended.address}</p>
                      )}

                      <div className="facility-actions">
                        <button className="btn btn-success">
                          <Navigation size={18} />
                          <span>Get Directions</span>
                        </button>
                        {result.recommended.url && (
                          <a
                            href={result.recommended.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-secondary"
                          >
                            <ExternalLink size={18} />
                            <span>Visit Website</span>
                          </a>
                        )}
                      </div>
                    </div>

                    <div className="cost-card">
                      <div className="cost-label">Your estimated cost</div>
                      <div className="cost-amount">${result.recommended.your_cost}</div>
                      {getSavingsVsER() > 0 && (
                        <div className="cost-savings">Save ${getSavingsVsER()} vs ER</div>
                      )}
                    </div>
                  </div>

                  {/* Why Recommended */}
                  {result.reasoning && result.reasoning.length > 0 && (
                    <div className="reasoning-section">
                      <h3 className="reasoning-title">Why we recommend this</h3>
                      <ul className="reasoning-list">
                        {result.reasoning.map((reason, i) => (
                          <li key={i} className="reasoning-item">
                            <CheckCircle2 size={16} className="reasoning-icon" />
                            <span>{reason}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Why Not ER */}
                  {result.why_not_er && (
                    <div className="info-box">
                      <Info size={18} className="info-box-icon" />
                      <div>
                        <span className="info-box-title">Why not the ER?</span>
                        <p className="info-box-text">{result.why_not_er}</p>
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {/* Alternatives */}
              {result.alternatives && result.alternatives.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <h3 className="alternatives-title">Other options nearby</h3>

                  <div className="alternatives-grid">
                    {result.alternatives.map((alt, i) => (
                      <motion.div
                        key={`${alt.name}-${i}`}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 + i * 0.1 }}
                        className="glass-card alternative-card"
                        whileHover={{
                          scale: 1.02,
                          background: 'rgba(255, 255, 255, 0.08)'
                        }}
                      >
                        <div className="alternative-content">
                          <div>
                            <div className="alternative-header">
                              <Building2 size={18} className="icon-primary" />
                              {alt.data_source && (
                                <span className={`source-badge ${alt.data_source === 'agent_scraped' ? 'verified' : 'estimated'}`}>
                                  {alt.data_source === 'agent_scraped' ? 'verified' : 'estimated'}
                                </span>
                              )}
                            </div>
                            <h4 className="alternative-name">{alt.name}</h4>
                            <div className="alternative-meta">
                              {alt.distance_miles != null && (
                                <span>{typeof alt.distance_miles === 'number' ? alt.distance_miles.toFixed(1) : alt.distance_miles} mi</span>
                              )}
                              {alt.wait_time && <span>{alt.wait_time}</span>}
                            </div>
                          </div>
                          <div className="alternative-cost">
                            <div className={`alternative-price ${getPriceClass(alt.your_cost)}`}>
                              ${alt.your_cost}
                            </div>
                            <ChevronRight size={20} className="icon-muted" />
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Disclaimer */}
              {result.disclaimer && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 }}
                  className="disclaimer"
                >
                  <strong>Disclaimer:</strong> {result.disclaimer}
                </motion.div>
              )}

              {/* Processing Time */}
              {result.processing_time_ms && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.7 }}
                  className="processing-time"
                >
                  Processed in {(result.processing_time_ms / 1000).toFixed(2)} seconds
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty State */}
        {!loading && !result && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="empty-state"
          >
            <div className="features-grid">
              {[
                { icon: DollarSign, title: 'Save Money', desc: 'Compare prices across facilities' },
                { icon: Clock, title: 'Save Time', desc: 'See real-time wait times' },
                { icon: Shield, title: 'Insurance Smart', desc: 'Find in-network providers' }
              ].map((feature) => (
                <div key={feature.title} className="glass-card feature-card">
                  <div className="feature-icon-wrapper">
                    <feature.icon size={24} className="icon-primary" />
                  </div>
                  <h3 className="feature-title">{feature.title}</h3>
                  <p className="feature-description">{feature.desc}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </main>
  );
}
