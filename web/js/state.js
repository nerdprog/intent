/**
 * StudyCrafter State Management
 * Handles student profile, topic masteries, active practice questions, and session persistence.
 */

class AppState {
  constructor() {
    this.STORAGE_KEY = 'studycrafter_state_v1';
    this.listeners = [];
    this.init();
  }

  init() {
    const saved = localStorage.getItem(this.STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        this.student = parsed.student || this.getDefaultStudent();
        this.mastery = parsed.mastery || this.getDefaultMastery();
        this.chatHistory = parsed.chatHistory || [];
        this.activeQuestion = parsed.activeQuestion || null;
      } catch (e) {
        console.warn('Failed to parse saved state, resetting to defaults:', e);
        this.resetDefaults();
      }
    } else {
      this.resetDefaults();
    }

    this.currentAgent = 'SUPERVISOR';
    this.isWorking = false;
    this.selectedTopic = this.student.selectedTopic || 'Probability';
  }

  getDefaultStudent() {
    const randomId = 'student_' + Math.random().toString(36).substring(2, 9);
    return {
      student_id: randomId,
      name: 'Nivetha',
      goal: 'Crack placement aptitude test',
      days_remaining: 10,
      daily_hours: 2,
      current_level: 'Beginner',
      selectedTopic: 'Probability'
    };
  }

  getDefaultMastery() {
    const masteryMap = {};
    CONFIG.TOPICS.forEach(t => {
      masteryMap[t.name] = t.defaultMastery;
    });
    return masteryMap;
  }

  resetDefaults() {
    this.student = this.getDefaultStudent();
    this.mastery = this.getDefaultMastery();
    this.chatHistory = [];
    this.activeQuestion = null;
    this.save();
  }

  save() {
    try {
      const data = {
        student: this.student,
        mastery: this.mastery,
        chatHistory: this.chatHistory,
        activeQuestion: this.activeQuestion
      };
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
      this.notify();
    } catch (e) {
      console.error('Failed to save state to localStorage:', e);
    }
  }

  // Subscribe to state changes
  subscribe(callback) {
    this.listeners.push(callback);
  }

  notify() {
    this.listeners.forEach(cb => cb(this));
  }

  // Profile Methods
  updateProfile(fields) {
    this.student = { ...this.student, ...fields };
    this.save();
  }

  setStudentId(newId) {
    if (newId && newId.trim()) {
      this.student.student_id = newId.trim();
      this.save();
    }
  }

  // Mastery Methods
  getMasteryForTopic(topicName) {
    if (!topicName) return 40;
    // Fuzzy match topic
    const foundKey = Object.keys(this.mastery).find(
      k => k.toLowerCase() === topicName.toLowerCase() || topicName.toLowerCase().includes(k.toLowerCase())
    );
    return foundKey ? this.mastery[foundKey] : (this.mastery[topicName] || 40);
  }

  updateMastery(topicName, newMastery) {
    if (!topicName) return;
    const key = Object.keys(this.mastery).find(
      k => k.toLowerCase() === topicName.toLowerCase() || topicName.toLowerCase().includes(k.toLowerCase())
    ) || topicName;

    const clamped = Math.max(0, Math.min(100, Math.round(newMastery)));
    this.mastery[key] = clamped;
    this.save();
  }

  applyMasteryDelta(topicName, delta) {
    const current = this.getMasteryForTopic(topicName);
    this.updateMastery(topicName, current + delta);
  }

  getOverallMastery() {
    const values = Object.values(this.mastery);
    if (!values.length) return 40;
    const sum = values.reduce((a, b) => a + b, 0);
    return Math.round(sum / values.length);
  }

  // Active Practice Question Management (Fixes Gap #1)
  setActivePracticeQuestion(questionData) {
    this.activeQuestion = {
      id: 'q_' + Date.now(),
      question: questionData.question,
      options: questionData.options || [],
      correct_answer: (questionData.correct_answer || '').trim().toUpperCase(),
      difficulty: questionData.difficulty || 'Medium',
      topic: questionData.topic || this.selectedTopic || 'Probability',
      submitted_answer: null,
      is_graded: false,
      is_correct: null
    };
    this.save();
  }

  getActivePracticeQuestion() {
    return this.activeQuestion;
  }

  clearActivePracticeQuestion() {
    this.activeQuestion = null;
    this.save();
  }

  // Chat History Management
  addMessage(msg) {
    const messageObj = {
      id: 'msg_' + Date.now() + '_' + Math.random().toString(36).substring(2, 5),
      timestamp: new Date().toISOString(),
      ...msg
    };
    this.chatHistory.push(messageObj);
    this.save();
    return messageObj;
  }

  clearChat() {
    this.chatHistory = [];
    this.activeQuestion = null;
    this.save();
  }

  // Agent State
  setAgentWorking(isWorking, agentKey = 'SUPERVISOR') {
    this.isWorking = isWorking;
    if (agentKey) this.currentAgent = agentKey;
    this.notify();
  }
}

window.AppState = new AppState();
