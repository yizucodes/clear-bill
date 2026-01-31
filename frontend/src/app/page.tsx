'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  MapPin,
  Upload,
  Clock,
  DollarSign,
  Star,
  Phone,
  Navigation,
  CheckCircle2,
  Loader2,
  Sparkles,
  Shield,
  AlertCircle,
  ChevronRight,
  Heart,
  Stethoscope,
  Building2,
  Video
} from 'lucide-react';

// Types
interface Facility {
  name: string;
  your_cost: number;
  distance: number;
  wait_time: string;
  rating: number;
  why_recommended: string[];
  address: string;
  phone: string;
  hours: string;
  facility_type: 'urgent_care' | 'emergency_room' | 'virtual_care' | 'primary_care';
}

interface Alternative {
  name: string;
  cost: number;
  distance: number;
  wait_time: string;
  facility_type: string;
}

interface AgentStep {
  step: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  duration: number;
  message: string;
}

interface RecommendationResult {
  recommended_facility: Facility;
  alternatives: Alternative[];
  agent_steps: AgentStep[];
  urgency_level: 'low' | 'medium' | 'high' | 'emergency';
  urgency_explanation: string;
  savings_vs_er: number;
}

const facilityIcons = {
  urgent_care: Building2,
  emergency_room: Heart,
  virtual_care: Video,
  primary_care: Stethoscope
};

const urgencyColors = {
  low: { bg: 'rgba(16, 185, 129, 0.1)', text: '#10b981', label: 'Low Urgency' },
  medium: { bg: 'rgba(245, 158, 11, 0.1)', text: '#f59e0b', label: 'Medium Urgency' },
  high: { bg: 'rgba(239, 68, 68, 0.1)', text: '#ef4444', label: 'High Urgency' },
  emergency: { bg: 'rgba(239, 68, 68, 0.2)', text: '#dc2626', label: 'Emergency' }
};

export default function Home() {
  const [symptoms, setSymptoms] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecommendationResult | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { label: 'Analyzing symptoms', icon: Stethoscope },
    { label: 'Checking insurance', icon: Shield },
    { label: 'Finding facilities', icon: MapPin },
    { label: 'Comparing prices', icon: DollarSign }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symptoms.trim()) return;

    setLoading(true);
    setResult(null);
    setCurrentStep(0);

    // Simulate step progression
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev >= steps.length - 1) {
          clearInterval(stepInterval);
          return prev;
        }
        return prev + 1;
      });
    }, 500);

    try {
      const response = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symptoms: symptoms.trim(),
          location: location.trim() || 'San Francisco, CA',
          insurance: null // Will be populated when OCR is used
        })
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error getting recommendation:', error);
    } finally {
      clearInterval(stepInterval);
      setLoading(false);
    }
  };

  return (
    <main style={{ minHeight: '100vh', padding: '2rem 0' }}>
      {/* Hero Section */}
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{ textAlign: 'center', marginBottom: '3rem' }}
        >
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 1rem',
            background: 'rgba(99, 102, 241, 0.1)',
            borderRadius: '9999px',
            marginBottom: '1.5rem'
          }}>
            <Sparkles size={16} style={{ color: '#818cf8' }} />
            <span style={{ fontSize: '0.875rem', color: '#a5b4fc', fontWeight: 500 }}>
              AI-Powered Healthcare Navigator
            </span>
          </div>

          <h1 style={{
            fontSize: 'clamp(2.5rem, 5vw, 4rem)',
            fontWeight: 800,
            lineHeight: 1.1,
            marginBottom: '1rem'
          }}>
            <span className="text-gradient">ClearBill</span>
            <span style={{ color: 'white' }}> Advisor</span>
          </h1>

          <p style={{
            fontSize: '1.25rem',
            color: '#94a3b8',
            maxWidth: '600px',
            margin: '0 auto'
          }}>
            Find the right care at the right price. We analyze your symptoms and insurance
            to recommend the best, most affordable care option.
          </p>
        </motion.div>

        {/* Search Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="glass-card"
          style={{
            maxWidth: '800px',
            margin: '0 auto 2rem',
            padding: '2rem'
          }}
        >
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '1.5rem' }}>
              <label className="label">What symptoms are you experiencing?</label>
              <div style={{ position: 'relative' }}>
                <Search
                  size={20}
                  style={{
                    position: 'absolute',
                    left: '1rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: '#6b7280'
                  }}
                />
                <input
                  type="text"
                  className="input input-dark"
                  placeholder="e.g., twisted ankle, sore throat, headache..."
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  style={{ paddingLeft: '3rem' }}
                />
              </div>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              marginBottom: '1.5rem'
            }}>
              <div>
                <label className="label">Your location</label>
                <div style={{ position: 'relative' }}>
                  <MapPin
                    size={20}
                    style={{
                      position: 'absolute',
                      left: '1rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: '#6b7280'
                    }}
                  />
                  <input
                    type="text"
                    className="input input-dark"
                    placeholder="San Francisco, CA"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    style={{ paddingLeft: '3rem' }}
                  />
                </div>
              </div>

              <div>
                <label className="label">Insurance card (optional)</label>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{
                    width: '100%',
                    justifyContent: 'flex-start',
                    padding: '0.875rem 1rem'
                  }}
                >
                  <Upload size={20} />
                  <span>Upload card photo</span>
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !symptoms.trim()}
              style={{ width: '100%', padding: '1rem' }}
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
              className="glass-card"
              style={{
                maxWidth: '500px',
                margin: '0 auto 2rem',
                padding: '2rem'
              }}
            >
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem'
              }}>
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
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '1rem',
                        padding: '0.75rem 1rem',
                        background: isActive ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                        borderRadius: 'var(--radius-lg)',
                        transition: 'all 0.3s ease'
                      }}
                    >
                      <div style={{
                        width: '2.5rem',
                        height: '2.5rem',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: isComplete
                          ? 'linear-gradient(135deg, #10b981 0%, #34d399 100%)'
                          : isActive
                            ? 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)'
                            : 'rgba(255, 255, 255, 0.1)'
                      }}>
                        {isComplete ? (
                          <CheckCircle2 size={20} color="white" />
                        ) : isActive ? (
                          <Loader2 size={20} color="white" className="animate-spin" />
                        ) : (
                          <Icon size={20} style={{ color: '#6b7280' }} />
                        )}
                      </div>
                      <span style={{
                        color: isActive || isComplete ? 'white' : '#6b7280',
                        fontWeight: isActive ? 600 : 400
                      }}>
                        {step.label}
                      </span>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {result && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              style={{ maxWidth: '900px', margin: '0 auto' }}
            >
              {/* Urgency Banner */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 }}
                style={{
                  background: urgencyColors[result.urgency_level].bg,
                  border: `1px solid ${urgencyColors[result.urgency_level].text}30`,
                  borderRadius: 'var(--radius-xl)',
                  padding: '1rem 1.5rem',
                  marginBottom: '1.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem'
                }}
              >
                <AlertCircle size={20} style={{ color: urgencyColors[result.urgency_level].text }} />
                <div>
                  <span style={{
                    fontWeight: 600,
                    color: urgencyColors[result.urgency_level].text
                  }}>
                    {urgencyColors[result.urgency_level].label}:
                  </span>
                  <span style={{ color: '#e2e8f0', marginLeft: '0.5rem' }}>
                    {result.urgency_explanation}
                  </span>
                </div>
              </motion.div>

              {/* Main Recommendation Card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                style={{
                  background: 'linear-gradient(145deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%)',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  borderRadius: 'var(--radius-2xl)',
                  padding: '2rem',
                  marginBottom: '1.5rem'
                }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  marginBottom: '1rem'
                }}>
                  <Sparkles size={16} style={{ color: '#818cf8' }} />
                  <span style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#a5b4fc',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    Best Match for You
                  </span>
                </div>

                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  flexWrap: 'wrap',
                  gap: '1.5rem'
                }}>
                  <div>
                    <h2 style={{
                      fontSize: '1.75rem',
                      fontWeight: 700,
                      color: 'white',
                      marginBottom: '0.5rem'
                    }}>
                      {result.recommended_facility.name}
                    </h2>

                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      flexWrap: 'wrap',
                      marginBottom: '1rem'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Star size={16} fill="#fbbf24" color="#fbbf24" />
                        <span style={{ color: '#fbbf24', fontWeight: 600 }}>
                          {result.recommended_facility.rating}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <MapPin size={16} style={{ color: '#94a3b8' }} />
                        <span style={{ color: '#94a3b8' }}>
                          {result.recommended_facility.distance} miles
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Clock size={16} style={{ color: '#94a3b8' }} />
                        <span style={{ color: '#94a3b8' }}>
                          ~{result.recommended_facility.wait_time} wait
                        </span>
                      </div>
                    </div>

                    <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>
                      {result.recommended_facility.address}
                    </p>

                    <div style={{
                      display: 'flex',
                      gap: '0.75rem',
                      flexWrap: 'wrap'
                    }}>
                      <button className="btn btn-success">
                        <Navigation size={18} />
                        <span>Get Directions</span>
                      </button>
                      <button className="btn btn-secondary">
                        <Phone size={18} />
                        <span>Call Now</span>
                      </button>
                    </div>
                  </div>

                  <div style={{
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    borderRadius: 'var(--radius-xl)',
                    padding: '1.5rem',
                    textAlign: 'center',
                    minWidth: '180px'
                  }}>
                    <div style={{
                      fontSize: '0.875rem',
                      color: '#34d399',
                      marginBottom: '0.25rem'
                    }}>
                      Your estimated cost
                    </div>
                    <div style={{
                      fontSize: '2.5rem',
                      fontWeight: 800,
                      color: '#10b981'
                    }}>
                      ${result.recommended_facility.your_cost}
                    </div>
                    <div style={{
                      fontSize: '0.875rem',
                      color: '#34d399'
                    }}>
                      Save ${result.savings_vs_er} vs ER
                    </div>
                  </div>
                </div>

                {/* Why Recommended */}
                <div style={{
                  marginTop: '1.5rem',
                  paddingTop: '1.5rem',
                  borderTop: '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                  <h3 style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#a5b4fc',
                    marginBottom: '0.75rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    Why we recommend this
                  </h3>
                  <ul style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                    gap: '0.5rem',
                    listStyle: 'none',
                    padding: 0,
                    margin: 0
                  }}>
                    {result.recommended_facility.why_recommended.map((reason, i) => (
                      <li
                        key={i}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          color: '#e2e8f0'
                        }}
                      >
                        <CheckCircle2 size={16} style={{ color: '#10b981', flexShrink: 0 }} />
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </motion.div>

              {/* Alternatives */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <h3 style={{
                  fontSize: '1rem',
                  fontWeight: 600,
                  color: '#94a3b8',
                  marginBottom: '1rem'
                }}>
                  Other options nearby
                </h3>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                  gap: '1rem'
                }}>
                  {result.alternatives.map((alt, i) => {
                    const Icon = facilityIcons[alt.facility_type as keyof typeof facilityIcons] || Building2;

                    return (
                      <motion.div
                        key={alt.name}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 + i * 0.1 }}
                        className="glass-card"
                        style={{
                          padding: '1.5rem',
                          cursor: 'pointer',
                          transition: 'all 0.3s ease'
                        }}
                        whileHover={{
                          scale: 1.02,
                          background: 'rgba(255, 255, 255, 0.08)'
                        }}
                      >
                        <div style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start'
                        }}>
                          <div>
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.5rem',
                              marginBottom: '0.25rem'
                            }}>
                              <Icon size={18} style={{ color: '#818cf8' }} />
                              <span style={{
                                fontSize: '0.75rem',
                                color: '#94a3b8',
                                textTransform: 'capitalize'
                              }}>
                                {alt.facility_type.replace('_', ' ')}
                              </span>
                            </div>
                            <h4 style={{
                              fontSize: '1.125rem',
                              fontWeight: 600,
                              color: 'white',
                              marginBottom: '0.5rem'
                            }}>
                              {alt.name}
                            </h4>
                            <div style={{
                              display: 'flex',
                              gap: '1rem',
                              color: '#94a3b8',
                              fontSize: '0.875rem'
                            }}>
                              <span>{alt.distance} mi</span>
                              <span>{alt.wait_time}</span>
                            </div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{
                              fontSize: '1.5rem',
                              fontWeight: 700,
                              color: alt.cost > 300 ? '#f87171' : '#fbbf24'
                            }}>
                              ${alt.cost}
                            </div>
                            <ChevronRight size={20} style={{ color: '#6b7280' }} />
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty State */}
        {!loading && !result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            style={{
              textAlign: 'center',
              marginTop: '3rem',
              color: '#64748b'
            }}
          >
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1.5rem',
              maxWidth: '700px',
              margin: '0 auto'
            }}>
              {[
                { icon: DollarSign, title: 'Save Money', desc: 'Compare prices across facilities' },
                { icon: Clock, title: 'Save Time', desc: 'See real-time wait times' },
                { icon: Shield, title: 'Insurance Smart', desc: 'Find in-network providers' }
              ].map((feature, i) => (
                <div
                  key={feature.title}
                  className="glass-card"
                  style={{ padding: '1.5rem', textAlign: 'center' }}
                >
                  <div style={{
                    width: '3rem',
                    height: '3rem',
                    margin: '0 auto 1rem',
                    borderRadius: '50%',
                    background: 'rgba(99, 102, 241, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <feature.icon size={24} style={{ color: '#818cf8' }} />
                  </div>
                  <h3 style={{ color: 'white', marginBottom: '0.25rem' }}>{feature.title}</h3>
                  <p style={{ fontSize: '0.875rem', color: '#94a3b8' }}>{feature.desc}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </main>
  );
}
