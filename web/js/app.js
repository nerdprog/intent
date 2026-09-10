/**
 * StudyCrafter Main Application Controller
 * Orchestrates UI events, chat workflow, live agent interactions, and practice question grading.
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const quickPillsContainer = document.getElementById('quick-pills');
  const masteryContainer = document.getElementById('mastery-list');
  const clearChatBtn = document.getElementById('btn-clear-chat');
  
  // Profile Elements
  const inputStudentName = document.getElementById('profile-name');
  const inputStudentGoal = document.getElementById('profile-goal');
  const inputDaysRemaining = document.getElementById('profile-days');
  const inputDailyHours = document.getElementById('profile-hours');
  const selectLevel = document.getElementById('profile-level');
  const inputStudentId = document.getElementById('profile-id');
  const btnResetId = document.getElementById('btn-reset-id');

  // Agent HUD Elements
  const hudDot = document.getElementById('hud-status-dot');
  const hudAgentName = document.getElementById('hud-agent-name');
  const hudAgentIcon = document.getElementById('hud-agent-icon');

  // Diagnostic Modal Elements
  const diagnosticModal = document.getElementById('diagnostic-modal');
  const diagnosticBody = document.getElementById('diagnostic-body');
  const btnCloseDiag = document.getElementById('btn-close-diag');

  let currentDiagQuestions = [];
  let currentDiagAnswers = {};

  // ==========================================================================
  // Initialization
  // ==========================================================================

  function initApp() {
    loadProfileToUI();
    renderMasteryUI();
    renderPills();
    renderChatHistory();

    // Welcome message if chat history is empty
    if (AppState.chatHistory.length === 0) {
      addWelcomeMessage();
    }

    attachEventListeners();
    updateHUD('SUPERVISOR', false);
  }

  function loadProfileToUI() {
    const s = AppState.student;
    if (inputStudentName) inputStudentName.value = s.name || '';
    if (inputStudentGoal) inputStudentGoal.value = s.goal || '';
    if (inputDaysRemaining) inputDaysRemaining.value = s.days_remaining || 10;
    if (inputDailyHours) inputDailyHours.value = s.daily_hours || 2;
    if (selectLevel) selectLevel.value = s.current_level || 'Beginner';
    if (inputStudentId) inputStudentId.value = s.student_id || '';
  }

  function renderMasteryUI() {
    if (masteryContainer) {
      masteryContainer.innerHTML = RenderEngine.renderMasteryList(AppState.mastery, AppState.selectedTopic);
    }
  }

  function renderPills() {
    if (!quickPillsContainer) return;
    quickPillsContainer.innerHTML = `
      <span class="pill-label">Suggested:</span>
      ${CONFIG.QUICK_PROMPTS.map(p => `
        <button class="prompt-pill" onclick="window.sendQuickPrompt('${p.prompt}', ${p.topic ? `'${p.topic}'` : 'null'})">
          ✨ ${p.label}
        </button>
      `).join('')}
    `;
  }

  function renderChatHistory() {
    if (!chatMessages) return;
    chatMessages.innerHTML = '';
    AppState.chatHistory.forEach(msg => {
      chatMessages.insertAdjacentHTML('beforeend', RenderEngine.renderChatMessage(msg));
    });
    scrollToBottom();
  }

  function addWelcomeMessage() {
    const welcomeText = `👋 **Hello ${AppState.student.name || 'there'}! Welcome to StudyCrafter.**\n\nI am your **AI Aptitude Tutor**, powered by a multi-agent system with live Knowledge Base RAG. I can help you prepare for campus placement tests and competitive exams.\n\n### What would you like to do?\n- 📚 **Learn a Topic**: Ask me to teach *Probability*, *Percentages*, *Time and Work*, etc.\n- 📝 **Practice Questions**: Ask for practice problems with clickable options and instant grading.\n- 🩺 **Take a Diagnostic**: Test your baseline across 5 key aptitude domains.\n- 📈 **Track Mastery**: Watch your mastery score adapt dynamically as you solve questions!`;

    AppState.addMessage({
      role: 'assistant',
      content: welcomeText,
      action: 'TEACH',
      topic: null
    });
    renderChatHistory();
  }

  function scrollToBottom() {
    if (chatMessages) {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }

  function updateHUD(agentKey, isWorking) {
    const agent = CONFIG.AGENTS[agentKey] || CONFIG.AGENTS.SUPERVISOR;
    if (hudDot) {
      hudDot.className = `agent-status-dot ${isWorking ? 'working' : ''}`;
    }
    if (hudAgentName) {
      hudAgentName.textContent = isWorking ? `${agent.name} (Thinking...)` : agent.name;
    }
    if (hudAgentIcon) {
      hudAgentIcon.textContent = agent.icon;
    }
  }

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '✅' : type === 'error' ? '⚠️' : 'ℹ️';
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // ==========================================================================
  // Event Listeners
  // ==========================================================================

  function attachEventListeners() {
    // Chat Submit via Form & Enter Key
    if (chatForm) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;
        chatInput.value = '';
        handleSendMessage(text);
      });
    }

    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          const text = chatInput.value.trim();
          if (!text) return;
          chatInput.value = '';
          handleSendMessage(text);
        }
      });
    }

    // Profile Form auto-save
    [inputStudentName, inputStudentGoal, inputDaysRemaining, inputDailyHours, selectLevel].forEach(el => {
      if (el) {
        el.addEventListener('change', () => {
          AppState.updateProfile({
            name: inputStudentName.value,
            goal: inputStudentGoal.value,
            days_remaining: Number(inputDaysRemaining.value),
            daily_hours: Number(inputDailyHours.value),
            current_level: selectLevel.value
          });
          showToast('Profile updated & saved', 'success');
        });
      }
    });

    // Student ID change / Reset
    if (inputStudentId) {
      inputStudentId.addEventListener('change', () => {
        AppState.setStudentId(inputStudentId.value);
        showToast('Student ID updated', 'info');
      });
    }

    if (btnResetId) {
      btnResetId.addEventListener('click', () => {
        const newId = 'student_' + Math.random().toString(36).substring(2, 9);
        inputStudentId.value = newId;
        AppState.setStudentId(newId);
        showToast('Generated new session ID: ' + newId, 'success');
      });
    }

    // Clear Chat
    if (clearChatBtn) {
      clearChatBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear your conversation history? Your profile and mastery levels will be kept.')) {
          AppState.clearChat();
          renderChatHistory();
          addWelcomeMessage();
          showToast('Chat history cleared', 'info');
        }
      });
    }

    // Diagnostic Modal Close
    if (btnCloseDiag) {
      btnCloseDiag.addEventListener('click', closeDiagnosticModal);
    }
  }

  // ==========================================================================
  // Core Chat & Webhook Execution
  // ==========================================================================

  async function handleSendMessage(messageText, options = {}) {
    const topic = options.topic || AppState.selectedTopic || null;
    const mastery = AppState.getMasteryForTopic(topic);
    const gradingAnswer = options.answer || null;
    const gradingCorrectAnswer = options.correct_answer || null;

    // 1. Add User message to UI and State
    const userMsg = AppState.addMessage({
      role: 'user',
      content: messageText
    });
    chatMessages.insertAdjacentHTML('beforeend', RenderEngine.renderChatMessage(userMsg));
    scrollToBottom();

    // 2. Show Typing Indicator
    const typingId = 'typing_' + Date.now();
    const typingHtml = `
      <div class="chat-message assistant" id="${typingId}">
        <div class="chat-avatar">🤖</div>
        <div class="message-content-wrapper">
          <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
          </div>
        </div>
      </div>
    `;
    chatMessages.insertAdjacentHTML('beforeend', typingHtml);
    scrollToBottom();

    // Disable send button while waiting
    if (sendBtn) sendBtn.disabled = true;
    updateHUD('SUPERVISOR', true);

    try {
      // 3. Send request to n8n Webhook
      const response = await ApiClient.sendMessage({
        student_id: AppState.student.student_id,
        message: messageText,
        topic: topic,
        mastery: mastery,
        answer: gradingAnswer,
        correct_answer: gradingCorrectAnswer
      });

      // Remove typing indicator
      const typingEl = document.getElementById(typingId);
      if (typingEl) typingEl.remove();

      // 4. Process Agent Response
      processAgentResponse(response, options);

    } catch (err) {
      console.error('Error handling message:', err);
      const typingEl = document.getElementById(typingId);
      if (typingEl) typingEl.remove();

      // Add Error Message
      const errorMsg = AppState.addMessage({
        role: 'assistant',
        content: `⚠️ **Connection Error:** Could not reach the n8n agent brain.\n\n*Details:* ${err.message}\n\nPlease check your connection or retry in a moment.`,
        action: 'UNKNOWN'
      });
      chatMessages.insertAdjacentHTML('beforeend', RenderEngine.renderChatMessage(errorMsg));
      scrollToBottom();
      showToast('Request failed: ' + err.message, 'error');
    } finally {
      if (sendBtn) sendBtn.disabled = false;
      updateHUD(AppState.currentAgent, false);
    }
  }

  /**
   * Process and render response payload from the n8n Multi-Agent system
   */
  function processAgentResponse(response, requestOptions = {}) {
    const action = (response.action || 'TEACH').toUpperCase();
    AppState.currentAgent = action;
    const respTopic = response.topic || AppState.selectedTopic;
    if (respTopic) AppState.selectedTopic = respTopic;

    let questionData = null;
    let diagnosticData = null;
    let isGraded = false;
    let submittedAnswer = null;
    let isCorrect = null;

    // Raw agent output normalization
    const agentOut = response.agent_output || {};
    const innerOutput = agentOut.output || agentOut;

    // --- Action Handler: PRACTICE (Question generation) ---
    if (action === 'PRACTICE' || innerOutput.question) {
      const q = innerOutput.question ? innerOutput : (agentOut.question ? agentOut : null);
      if (q && q.question && q.options) {
        questionData = {
          question: q.question,
          options: q.options,
          correct_answer: (q.correct_answer || '').trim().toUpperCase(),
          difficulty: q.difficulty || 'Medium',
          topic: q.topic || respTopic || 'Probability'
        };
        // Store in state so option clicks can grade it (Fixes Gap #1)
        AppState.setActivePracticeQuestion(questionData);
      }
    }

    // --- Action Handler: ASSESS (Grading answer) ---
    if (action === 'ASSESS' || innerOutput.correct !== undefined || agentOut.correct !== undefined) {
      const evalData = innerOutput.correct !== undefined ? innerOutput : agentOut;
      isGraded = true;
      isCorrect = Boolean(evalData.correct);
      submittedAnswer = evalData.submitted_answer || requestOptions.answer;
      
      // Update Mastery based on deterministic grading rules (+22% / -8%)
      const targetTopic = evalData.topic || respTopic || 'Probability';
      const delta = isCorrect ? 22 : -8;
      AppState.applyMasteryDelta(targetTopic, delta);
      renderMasteryUI();

      // If there was an active practice question, mark it graded in chat history
      const lastMsgWithQuestion = [...AppState.chatHistory].reverse().find(m => m.questionData && !m.isGraded);
      if (lastMsgWithQuestion) {
        lastMsgWithQuestion.isGraded = true;
        lastMsgWithQuestion.submittedAnswer = submittedAnswer;
        lastMsgWithQuestion.isCorrect = isCorrect;
        AppState.save();
        renderChatHistory();
      }
    }

    // --- Action Handler: PROGRESS (Mastery update) ---
    if (action === 'PROGRESS' || innerOutput.new_mastery !== undefined || agentOut.new_mastery !== undefined) {
      const prog = innerOutput.new_mastery !== undefined ? innerOutput : agentOut;
      if (prog.new_mastery !== undefined) {
        const targetTopic = prog.topic || respTopic;
        AppState.updateMastery(targetTopic, prog.new_mastery);
        renderMasteryUI();
      }
    }

    // --- Action Handler: DIAGNOSE (Diagnostic questions) ---
    if (action === 'DIAGNOSE' || innerOutput.diagnostic || agentOut.diagnostic) {
      diagnosticData = innerOutput.diagnostic || agentOut.diagnostic;
      currentDiagQuestions = [];
      if (Array.isArray(diagnosticData)) {
        diagnosticData.forEach(t => {
          (t.questions || []).forEach(q => {
            currentDiagQuestions.push({
              topic: t.topic,
              question: q.q || q.question,
              options: q.options,
              correct_answer: q.correct_answer
            });
          });
        });
      }
    }

    // 5. Add Assistant Response to Chat
    let textContent = response.response || (typeof innerOutput === 'string' ? innerOutput : '');
    
    if (!textContent || textContent === 'Processed action: PRACTICE.') {
      textContent = `Here is a practice question on **${respTopic || 'Aptitude'}** to test your problem-solving skills:`;
    } else if (textContent === 'Processed action: DIAGNOSE.') {
      textContent = `I have generated a multi-topic diagnostic test across 5 key aptitude domains.`;
    }

    const assistantMsg = AppState.addMessage({
      role: 'assistant',
      content: textContent,
      action: action,
      topic: respTopic,
      questionData: questionData,
      diagnosticData: diagnosticData,
      isGraded: isGraded,
      submittedAnswer: submittedAnswer,
      isCorrect: isCorrect
    });

    chatMessages.insertAdjacentHTML('beforeend', RenderEngine.renderChatMessage(assistantMsg));
    scrollToBottom();
  }

  // ==========================================================================
  // Global Window Functions (for UI handlers)
  // ==========================================================================

  // Handle Option Click from Practice Card (Clickable A, B, C, D)
  window.handleSelectOption = function(optionLetter, buttonElement) {
    const activeQ = AppState.getActivePracticeQuestion();
    if (!activeQ) {
      showToast('No active question to grade', 'error');
      return;
    }

    const topic = activeQ.topic || AppState.selectedTopic || 'Probability';
    const correctAns = activeQ.correct_answer;

    console.log(`[Practice Answer Clicked] Option: ${optionLetter}, Stored Correct: ${correctAns}`);

    // Send grading payload to n8n webhook
    handleSendMessage(`My answer is ${optionLetter}`, {
      topic: topic,
      answer: optionLetter,
      correct_answer: correctAns
    });
  };

  // Quick Prompt Trigger
  window.sendQuickPrompt = function(promptText, topicName) {
    if (topicName) {
      AppState.selectedTopic = topicName;
      renderMasteryUI();
    }
    handleSendMessage(promptText, { topic: topicName });
  };

  // Select Topic from Sidebar
  window.selectTopic = function(topicName) {
    AppState.selectedTopic = topicName;
    renderMasteryUI();
    showToast(`Active topic set to ${topicName}`, 'info');
    handleSendMessage(`Teach me ${topicName}`, { topic: topicName });
  };

  // Diagnostic Modal
  window.openDiagnosticModal = function() {
    if (!currentDiagQuestions.length) {
      showToast('Generating fresh diagnostic test...', 'info');
      handleSendMessage('I want to take a diagnostic assessment to test my skills');
      return;
    }

    currentDiagAnswers = {};
    if (diagnosticBody) {
      diagnosticBody.innerHTML = `
        <div style="font-size: 13.5px; color: var(--text-secondary); margin-bottom: 16px;">
          Answer these questions across 5 core topics to calculate your starting mastery levels:
        </div>
        ${currentDiagQuestions.map((q, qIndex) => `
          <div style="background: rgba(13, 18, 31, 0.8); border: 1px solid var(--border-subtle); border-radius: var(--border-radius-md); padding: 14px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
              <span class="badge-topic" style="font-size: 11px;">${q.topic}</span>
              <span style="font-size: 11px; color: var(--text-muted);">Q${qIndex + 1} of ${currentDiagQuestions.length}</span>
            </div>
            <p style="font-weight: 500; font-size: 14px; color: #ffffff; margin-bottom: 10px;">${q.question}</p>
            <div style="display: flex; flex-direction: column; gap: 6px;">
              ${(q.options || []).map((opt, optIndex) => `
                <label style="display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); cursor: pointer; padding: 6px 10px; background: rgba(255, 255, 255, 0.03); border-radius: 6px;">
                  <input type="radio" name="diag_q_${qIndex}" value="${opt}" onchange="window.saveDiagAnswer(${qIndex}, '${opt.replace(/'/g, "\\'")}')" />
                  <span>${opt}</span>
                </label>
              `).join('')}
            </div>
          </div>
        `).join('')}
        <button class="btn-primary" onclick="window.submitDiagnostic()">Submit Diagnostic & Calculate Mastery</button>
      `;
    }

    if (diagnosticModal) diagnosticModal.classList.add('active');
  };

  window.saveDiagAnswer = function(qIndex, selectedOpt) {
    currentDiagAnswers[qIndex] = selectedOpt;
  };

  window.submitDiagnostic = function() {
    let totalScore = 0;
    const topicScores = {};

    currentDiagQuestions.forEach((q, idx) => {
      const ans = currentDiagAnswers[idx];
      const isCorrect = (ans && ans.trim().toLowerCase() === (q.correct_answer || '').trim().toLowerCase());
      if (isCorrect) totalScore++;

      if (!topicScores[q.topic]) topicScores[q.topic] = { correct: 0, total: 0 };
      topicScores[q.topic].total++;
      if (isCorrect) topicScores[q.topic].correct++;
    });

    // Update mastery per topic
    Object.entries(topicScores).forEach(([tName, stats]) => {
      const calculated = Math.round((stats.correct / stats.total) * 100);
      AppState.updateMastery(tName, calculated);
    });

    renderMasteryUI();
    closeDiagnosticModal();

    showToast(`Diagnostic completed! Score: ${totalScore}/${currentDiagQuestions.length}`, 'success');

    handleSendMessage(`I completed the diagnostic assessment and scored ${totalScore} out of ${currentDiagQuestions.length}. Please evaluate my baseline and update my study plan.`);
  };

  function closeDiagnosticModal() {
    if (diagnosticModal) diagnosticModal.classList.remove('active');
  }

  // Start the application
  initApp();
});
