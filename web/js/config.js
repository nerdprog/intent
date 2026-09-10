/**
 * StudyCrafter Configuration & Constants
 */
const CONFIG = {
  // Live n8n Multi-Agent Backend Webhook URL
  WEBHOOK_URL: 'https://nivi0706.app.n8n.cloud/webhook/studycrafter',
  
  // Timeout for webhook calls (ms)
  REQUEST_TIMEOUT: 45000,
  
  // Core Aptitude Topics covered in the RAG corpus
  TOPICS: [
    { id: 'percentages', name: 'Percentages', defaultMastery: 45, icon: '📊' },
    { id: 'ratio', name: 'Ratio and Proportion', defaultMastery: 40, icon: '⚖️' },
    { id: 'averages', name: 'Averages', defaultMastery: 50, icon: '📈' },
    { id: 'time_work', name: 'Time and Work', defaultMastery: 35, icon: '⏱️' },
    { id: 'speed_distance', name: 'Time Speed and Distance', defaultMastery: 40, icon: '🚀' },
    { id: 'profit_loss', name: 'Profit and Loss', defaultMastery: 45, icon: '💰' },
    { id: 'probability', name: 'Probability', defaultMastery: 40, icon: '🎲' }
  ],
  
  // Agent Metadata Mapping
  AGENTS: {
    SUPERVISOR: {
      name: 'Supervisor Agent',
      icon: '🧭',
      desc: 'Multi-Agent Intent Router & Memory Coordinator',
      color: '#818cf8'
    },
    PROFILE: {
      name: 'Profile Agent',
      icon: '👤',
      desc: 'Extracts student goals and schedule',
      color: '#38bdf8'
    },
    DIAGNOSE: {
      name: 'Diagnostic Agent',
      icon: '🩺',
      desc: 'Multi-topic baseline diagnostic generator',
      color: '#06b6d4'
    },
    TEACH: {
      name: 'Tutor Agent',
      icon: '👨‍🏫',
      desc: 'Knowledge Base Grounded RAG Tutor',
      color: '#6366f1'
    },
    PRACTICE: {
      name: 'Assessment Agent',
      icon: '📝',
      desc: 'Aptitude Practice Question Generator',
      color: '#a855f7'
    },
    ASSESS: {
      name: 'Evaluator Agent',
      icon: '⚖️',
      desc: 'Deterministic Answer Grader',
      color: '#10b981'
    },
    PROGRESS: {
      name: 'Progress Agent',
      icon: '📈',
      desc: 'Adaptive Mastery Tracker (+22% / -8%)',
      color: '#f59e0b'
    },
    REPLAN: {
      name: 'Replanner Agent',
      icon: '🔄',
      desc: 'Adaptive Curriculum Scheduler',
      color: '#ec4899'
    },
    UNKNOWN: {
      name: 'StudyCrafter AI',
      icon: '🤖',
      desc: 'Multi-Agent Assistant',
      color: '#94a3b8'
    }
  },

  // Quick Action Suggestions for Students
  QUICK_PROMPTS: [
    { label: 'Teach Probability', prompt: 'Teach me Probability with concepts and formulas', topic: 'Probability' },
    { label: 'Practice Question', prompt: 'Give me a practice question on Probability', topic: 'Probability' },
    { label: 'Harder Question', prompt: 'Give me a harder question on this topic', topic: null },
    { label: 'Run Diagnostic', prompt: 'I want to take a diagnostic assessment across topics', topic: null },
    { label: 'Teach Percentages', prompt: 'Teach me Percentages and profit calculation formulas', topic: 'Percentages' },
    { label: 'Time & Work Question', prompt: 'Give me a practice question on Time and Work', topic: 'Time and Work' },
    { label: 'Check Progress', prompt: 'How is my overall progress and study plan?', topic: null }
  ]
};

// Export to global scope
window.CONFIG = CONFIG;
