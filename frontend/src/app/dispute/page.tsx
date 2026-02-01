'use client';

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileText,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Sparkles,
  Shield,
  DollarSign,
  AlertTriangle,
  Download,
  Copy,
  ChevronRight,
  X,
  File,
  Receipt,
  Scale,
  Send,
  ExternalLink,
  Building2,
  Briefcase,
  TrendingUp,
  PiggyBank
} from 'lucide-react';

// Types
interface LineItem {
  description: string;
  cpt_code?: string;
  icd_codes?: string[];
  amount?: number;
  status?: string;
  notes?: string;
}

interface BillingSummary {
  total_charges?: number;
  insurance_paid?: number;
  patient_paid?: number;
  amount_due?: number;
}

interface Issue {
  issue_type: string;
  title: string;
  description: string;
  severity: string;
  evidence?: string;
  recommended_action?: string;
}

interface ParsedBill {
  filename: string;
  facility_name?: string;
  patient_name?: string;
  date_of_service?: string;
  provider_name?: string;
  billing_summary?: BillingSummary;
  line_items?: LineItem[];
}

interface NextStepLink {
  name: string;
  url: string;
  title: string;
  type: string;
}

interface NextSteps {
  provider?: NextStepLink | null;
  insurance?: NextStepLink | null;
}

interface CoverageEstimate {
  expected_insurance_payment: number;
  expected_patient_responsibility: number;
  potential_savings: number;
  explanation: string;
  confidence: 'low' | 'medium' | 'high';
}

interface InsuranceInfo {
  insurance_name?: string;
  insurance_plan?: string;
  plan_type?: string;
  member_id?: string;
  group_number?: string;
}

interface AnalysisResult {
  bills: ParsedBill[];
  issues: Issue[];
  dispute_letter?: {
    subject: string;
    body: string;
  };
  next_steps?: NextSteps;
  insurance_info?: InsuranceInfo;
  coverage_estimate?: CoverageEstimate;
  total_billed: number;
  total_insurance_paid: number;
  total_patient_paid: number;
  total_due: number;
}

export default function DisputePage() {
  const [files, setFiles] = useState<File[]>([]);
  const [insuranceFile, setInsuranceFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const steps = [
    { label: 'Uploading documents', icon: Upload },
    { label: 'Parsing bills', icon: FileText },
    { label: 'Reading insurance card', icon: Shield },
    { label: 'Analyzing charges', icon: DollarSign },
    { label: 'Researching policies', icon: Scale },
    { label: 'Generating dispute', icon: Sparkles }
  ];

  // Use local API route (which proxies to Python backend if available)
  const BACKEND_URL = '';

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf' || file.type.startsWith('image/')
    );
    setFiles(prev => [...prev, ...droppedFiles]);
    setResult(null);
    setError(null);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...selectedFiles]);
      setResult(null);
      setError(null);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleInsuranceFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setInsuranceFile(e.target.files[0]);
    }
  };

  const removeInsuranceFile = () => {
    setInsuranceFile(null);
  };

  const handleAnalyze = async () => {
    if (files.length === 0) return;

    setLoading(true);
    setResult(null);
    setError(null);
    setCurrentStep(0);

    // Simulate step progression
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => (prev >= steps.length - 1 ? prev : prev + 1));
    }, 2000);

    try {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));

      // Add insurance card if uploaded
      if (insuranceFile) {
        formData.append('insurance_card', insuranceFile);
      }

      const response = await fetch(`${BACKEND_URL}/api/dispute/analyze`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      setCurrentStep(steps.length);

      if (!data.success) {
        setError(data.error || 'Failed to analyze bills');
      } else {
        setResult(data);
      }
    } catch (err) {
      console.error('Error:', err);
      setError('Failed to connect to dispute service. Make sure the backend is running.');

      // Demo data for testing UI
      setResult({
        bills: [
          {
            filename: 'Carbon-health-bill-010226.pdf',
            facility_name: 'Carbon Health',
            patient_name: 'Dhruv Miyani',
            date_of_service: 'January 2nd, 2026',
            provider_name: 'Katy Gutman, NP',
            billing_summary: {
              total_charges: 195.22,
              insurance_paid: 178.56,
              patient_paid: 15.00,
              amount_due: 1.66
            },
            line_items: [
              { description: 'Urinalysis', cpt_code: '81003', amount: 95.00, status: 'valid' },
              { description: 'Office visit, new patient', cpt_code: '99203', amount: 400.00, status: 'valid' }
            ]
          }
        ],
        issues: [
          {
            issue_type: 'billing_error',
            title: 'Math discrepancy in billing statement',
            description: 'Total charges ($195.22) do not match sum of services ($495.00). This may be due to insurance adjustments not being clearly labeled.',
            severity: 'low',
            evidence: 'Services: $95 + $400 = $495, but Total Charges shows $195.22',
            recommended_action: 'Request itemized explanation of total charges calculation'
          }
        ],
        dispute_letter: {
          subject: 'Billing Discrepancy - Account #29856939 - Service Date 01/02/2026',
          body: `January 31, 2026

Billing Department
Carbon Health

RE: Account #29856939
Patient Name: Dhruv Miyani
Date of Service: January 2, 2026

Dear Billing Department Representative,

I am writing to bring your attention to a mathematical discrepancy I have identified in the billing statement for services rendered on January 2, 2026.

Upon careful review, I have noticed that the total charges do not accurately reflect the sum of the individual services provided:

• Urinalysis (CPT 81003): $95.00
• Office visit, new patient (CPT 99203): $400.00
• Total of itemized services: $495.00
• Bill shows "Total Charges": $195.22
• Discrepancy: $299.78

I kindly request that you:
1. Review the billing calculations for this account
2. Provide a corrected or clarified billing statement
3. Explain the insurance adjustment methodology

Please respond in writing with your findings.

Sincerely,
Dhruv Miyani

Account #: 29856939
Date of Service: 01/02/2026`
        },
        total_billed: 330.20,
        total_insurance_paid: 298.54,
        total_patient_paid: 30.00,
        total_due: 1.66
      });
    } finally {
      clearInterval(stepInterval);
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (result?.dispute_letter) {
      navigator.clipboard.writeText(result.dispute_letter.body);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const downloadLetter = () => {
    if (result?.dispute_letter) {
      const blob = new Blob([`Subject: ${result.dispute_letter.subject}\n\n${result.dispute_letter.body}`], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'dispute_letter.txt';
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const severityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'severity-critical';
      case 'high': return 'severity-high';
      case 'medium': return 'severity-medium';
      default: return 'severity-low';
    }
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
            <Scale size={16} className="icon-primary" />
            <span className="hero-badge-text">AI-Powered Bill Dispute</span>
          </div>

          <h1 className="hero-title">
            <span className="text-gradient">Dispute</span>
            <span style={{ color: 'white' }}> Your Bills</span>
          </h1>

          <p className="hero-subtitle">
            Upload your medical bills and we&apos;ll analyze them for errors, overcharges,
            and generate a professional dispute letter for you.
          </p>
        </motion.div>

        {/* Upload Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="glass-card form-card"
        >
          {/* Drop Zone */}
          <div
            className="upload-dropzone"
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <input
              id="file-input"
              type="file"
              multiple
              accept=".pdf,image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Upload size={40} className="upload-icon" />
            <p className="upload-text">
              <span className="upload-text-highlight">Click to upload</span> or drag and drop
            </p>
            <p className="upload-subtext">PDF or image files (medical bills, EOBs)</p>
          </div>

          {/* Insurance Card Upload */}
          <div className="form-group">
            <label className="label">Your insurance card</label>
            {!insuranceFile ? (
              <div
                className="insurance-upload-zone"
                onClick={() => document.getElementById('insurance-input')?.click()}
              >
                <input
                  id="insurance-input"
                  type="file"
                  accept=".pdf,image/*"
                  onChange={handleInsuranceFileSelect}
                  className="hidden"
                />
                <Shield size={24} className="insurance-upload-icon" />
                <p className="insurance-upload-text">
                  <span className="upload-text-highlight">Upload insurance card</span>
                </p>
                <p className="insurance-upload-subtext">Photo or PDF of front of card</p>
              </div>
            ) : (
              <div className="insurance-file-display">
                <div className="insurance-file-info">
                  <Shield size={20} className="icon-primary" />
                  <span className="insurance-file-name">{insuranceFile.name}</span>
                  <span className="file-size">{(insuranceFile.size / 1024).toFixed(1)} KB</span>
                </div>
                <button
                  onClick={removeInsuranceFile}
                  className="file-remove"
                >
                  <X size={16} />
                </button>
              </div>
            )}
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="file-list">
              {files.map((file, index) => (
                <motion.div
                  key={`${file.name}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="file-item"
                >
                  <File size={18} className="icon-muted" />
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                    className="file-remove"
                  >
                    <X size={16} />
                  </button>
                </motion.div>
              ))}
            </div>
          )}

          {/* Analyze Button */}
          <button
            onClick={handleAnalyze}
            className="btn btn-primary btn-fullwidth"
            disabled={loading || files.length === 0}
          >
            {loading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                <span>Analyzing your bills...</span>
              </>
            ) : (
              <>
                <Sparkles size={20} />
                <span>Analyze Bills & Generate Dispute</span>
              </>
            )}
          </button>
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
                <h3 className="error-title">Error Analyzing Bills</h3>
                <p className="error-message">{error}</p>
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
              className="results-container"
            >
              {/* Summary Card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="recommendation-card"
              >
                <div className="recommendation-header">
                  <Receipt size={16} className="icon-primary" />
                  <span className="recommendation-label">Billing Summary</span>
                </div>

                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="summary-label">Total Billed</span>
                    <span className="summary-value">${result.total_billed.toFixed(2)}</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Insurance Paid</span>
                    <span className="summary-value text-green">${result.total_insurance_paid.toFixed(2)}</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">You Paid</span>
                    <span className="summary-value">${result.total_patient_paid.toFixed(2)}</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Amount Due</span>
                    <span className="summary-value text-yellow">${result.total_due.toFixed(2)}</span>
                  </div>
                </div>
              </motion.div>

              {/* Coverage Estimate */}
              {result.coverage_estimate && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 }}
                  className="glass-card coverage-estimate-card"
                >
                  <div className="coverage-header">
                    <div className="coverage-header-left">
                      <PiggyBank size={20} className="icon-success" />
                      <span className="coverage-title">Coverage Estimate</span>
                      {result.insurance_info?.plan_type && (
                        <span className="coverage-plan-badge">{result.insurance_info.plan_type}</span>
                      )}
                    </div>
                    <span className={`coverage-confidence ${result.coverage_estimate.confidence}`}>
                      {result.coverage_estimate.confidence} confidence
                    </span>
                  </div>

                  <div className="coverage-grid">
                    <div className="coverage-item">
                      <span className="coverage-label">Expected Insurance Payment</span>
                      <span className="coverage-value text-green">
                        ${result.coverage_estimate.expected_insurance_payment?.toFixed(2) || '0.00'}
                      </span>
                    </div>
                    <div className="coverage-item">
                      <span className="coverage-label">Your Expected Cost</span>
                      <span className="coverage-value">
                        ${result.coverage_estimate.expected_patient_responsibility?.toFixed(2) || '0.00'}
                      </span>
                    </div>
                    {result.coverage_estimate.potential_savings > 0 && (
                      <div className="coverage-item savings">
                        <span className="coverage-label">
                          <TrendingUp size={14} />
                          Potential Savings
                        </span>
                        <span className="coverage-value text-green">
                          ${result.coverage_estimate.potential_savings?.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>

                  {result.coverage_estimate.explanation && (
                    <p className="coverage-explanation">{result.coverage_estimate.explanation}</p>
                  )}

                  {result.insurance_info && (
                    <div className="insurance-details">
                      <span className="insurance-detail-label">Detected Insurance:</span>
                      <span className="insurance-detail-value">
                        {result.insurance_info.insurance_plan || result.insurance_info.insurance_name}
                      </span>
                      {result.insurance_info.member_id && (
                        <>
                          <span className="insurance-detail-label">Member ID:</span>
                          <span className="insurance-detail-value">{result.insurance_info.member_id}</span>
                        </>
                      )}
                    </div>
                  )}
                </motion.div>
              )}

              {/* Issues Found */}
              {result.issues.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <h3 className="section-title">
                    <AlertCircle size={20} className="icon-warning" />
                    Issues Found ({result.issues.length})
                  </h3>

                  <div className="issues-list">
                    {result.issues.map((issue, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 + i * 0.1 }}
                        className="glass-card issue-card"
                      >
                        <div className="issue-header">
                          <span className={`issue-severity ${severityColor(issue.severity)}`}>
                            {issue.severity.toUpperCase()}
                          </span>
                          <span className="issue-type">{issue.issue_type.replace('_', ' ')}</span>
                        </div>
                        <h4 className="issue-title">{issue.title}</h4>
                        <p className="issue-description">{issue.description}</p>
                        {issue.evidence && (
                          <div className="issue-evidence">
                            <strong>Evidence:</strong> {issue.evidence}
                          </div>
                        )}
                        {issue.recommended_action && (
                          <div className="issue-action">
                            <ChevronRight size={16} />
                            <span>{issue.recommended_action}</span>
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Parsed Bills */}
              {result.bills.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                >
                  <h3 className="section-title">
                    <FileText size={20} className="icon-muted" />
                    Parsed Bills ({result.bills.length})
                  </h3>

                  <div className="bills-list">
                    {result.bills.map((bill, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 + i * 0.1 }}
                        className="glass-card bill-card"
                      >
                        <div className="bill-header">
                          <div>
                            <h4 className="bill-facility">{bill.facility_name || 'Unknown Facility'}</h4>
                            <p className="bill-meta">
                              {bill.date_of_service} • {bill.provider_name || 'Unknown Provider'}
                            </p>
                          </div>
                          {bill.billing_summary && (
                            <div className="bill-amount">
                              ${bill.billing_summary.amount_due?.toFixed(2) || '0.00'}
                              <span className="bill-amount-label">due</span>
                            </div>
                          )}
                        </div>

                        {bill.line_items && bill.line_items.length > 0 && (
                          <div className="line-items">
                            {bill.line_items.map((item, j) => (
                              <div key={j} className="line-item">
                                <div className="line-item-info">
                                  <span className="line-item-desc">{item.description}</span>
                                  {item.cpt_code && (
                                    <span className="line-item-code">CPT: {item.cpt_code}</span>
                                  )}
                                </div>
                                <div className="line-item-amount">
                                  ${item.amount?.toFixed(2) || '0.00'}
                                  {item.status === 'valid' && (
                                    <CheckCircle2 size={14} className="text-green" />
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Next Steps - Dispute Links */}
              {result.next_steps && (result.next_steps.provider || result.next_steps.insurance) && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.55 }}
                >
                  <h3 className="section-title">
                    <ExternalLink size={20} className="icon-primary" />
                    Next Steps - File Your Dispute
                  </h3>

                  <div className="next-steps-grid">
                    {result.next_steps.provider && (
                      <a
                        href={result.next_steps.provider.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="glass-card next-step-card"
                      >
                        <div className="next-step-icon provider">
                          <Building2 size={24} />
                        </div>
                        <div className="next-step-content">
                          <span className="next-step-label">Step 1: Provider</span>
                          <h4 className="next-step-title">{result.next_steps.provider.name}</h4>
                          <p className="next-step-desc">File dispute with billing department</p>
                        </div>
                        <ExternalLink size={18} className="next-step-arrow" />
                      </a>
                    )}

                    {result.next_steps.insurance && (
                      <a
                        href={result.next_steps.insurance.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="glass-card next-step-card"
                      >
                        <div className="next-step-icon insurance">
                          <Briefcase size={24} />
                        </div>
                        <div className="next-step-content">
                          <span className="next-step-label">Step 2: Insurance</span>
                          <h4 className="next-step-title">{result.next_steps.insurance.name}</h4>
                          <p className="next-step-desc">File appeal with insurance company</p>
                        </div>
                        <ExternalLink size={18} className="next-step-arrow" />
                      </a>
                    )}
                  </div>
                </motion.div>
              )}

              {/* Dispute Letter */}
              {result.dispute_letter && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                >
                  <h3 className="section-title">
                    <Send size={20} className="icon-primary" />
                    Generated Dispute Letter
                  </h3>

                  <div className="glass-card dispute-letter-card">
                    <div className="dispute-letter-header">
                      <div className="dispute-letter-subject">
                        <strong>Subject:</strong> {result.dispute_letter.subject}
                      </div>
                      <div className="dispute-letter-actions">
                        <button onClick={copyToClipboard} className="btn btn-secondary btn-sm">
                          {copied ? <CheckCircle2 size={16} /> : <Copy size={16} />}
                          {copied ? 'Copied!' : 'Copy'}
                        </button>
                        <button onClick={downloadLetter} className="btn btn-secondary btn-sm">
                          <Download size={16} />
                          Download
                        </button>
                      </div>
                    </div>
                    <pre className="dispute-letter-body">{result.dispute_letter.body}</pre>
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty State */}
        {!loading && !result && files.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="empty-state"
          >
            <div className="features-grid">
              {[
                { icon: Shield, title: 'Find Errors', desc: 'Detect billing mistakes & overcharges' },
                { icon: Scale, title: 'Know Your Rights', desc: 'Research relevant policies' },
                { icon: FileText, title: 'Generate Letters', desc: 'Professional dispute documents' }
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
