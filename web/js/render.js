/**
 * StudyCrafter Render Engine
 * Handles markdown formatting, interactive question cards, diagnostic quizzes, and sidebar elements.
 */

const RenderEngine = {
  /**
   * Format basic markdown and math equations to safe HTML
   * @param {string} text
   * @returns {string} HTML string
   */
  formatMarkdown(text) {
    if (!text) return '';

    let html = text;

    // Escape basic HTML tags to prevent XSS
    html = html
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Format Headings
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h2>$1</h2>');

    // Bold & Italic
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');

    // Inline code & formulas
    html = html.replace(/`([^`]+)`/gim, '<code>$1</code>');

    // Highlight formulas with formula callout
    html = html.replace(/(?:^|\n)(Key formulas|Formulas?|Formula):\s*([\s\S]*?)(?=\n\n|\n[A-Z]|$)/gi, (match, title, content) => {
      return `<div class="formula-callout"><strong>📐 ${title}:</strong><br>${content.trim().replace(/\n/g, '<br>')}</div>`;
    });

    // Worked example boxes
    html = html.replace(/(?:^|\n)(Worked example|Example solution|Example):\s*([\s\S]*?)(?=\n\n|\n[A-Z]|$)/gi, (match, title, content) => {
      return `<div class="example-box"><div class="example-title">💡 ${title}</div>${content.trim().replace(/\n/g, '<br>')}</div>`;
    });

    // Unordered lists
    html = html.replace(/^\s*[-•]\s+(.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/gims, '<ul>$1</ul>');
    // Fix consecutive nested lists
    html = html.replace(/<\/ul>\s*<ul>/gim, '');

    // Paragraphs & Linebreaks
    html = html.replace(/\n\n+/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');

    return `<div class="markdown-body"><p>${html}</p></div>`;
  },

  /**
   * Render an interactive PRACTICE Question Card with 4 clickable option buttons
   * @param {Object} qData - Question object
   * @param {string} qData.question
   * @param {Array<string>} qData.options
   * @param {string} qData.correct_answer
   * @param {string} qData.difficulty
   * @param {string} qData.topic
   * @param {boolean} [isGraded=false]
   * @param {string} [submittedAnswer=null]
   * @param {boolean} [isCorrect=null]
   * @returns {string} HTML string
   */
  renderPracticeCard(qData, isGraded = false, submittedAnswer = null, isCorrect = null) {
    if (!qData || !qData.question) return '';

    const topic = qData.topic || 'Aptitude';
    const difficulty = (qData.difficulty || 'Medium').toLowerCase();
    const correctLetter = (qData.correct_answer || '').trim().toUpperCase();
    const subLetter = submittedAnswer ? submittedAnswer.trim().toUpperCase() : null;

    const optionsHtml = (qData.options || []).map((opt, index) => {
      const letters = ['A', 'B', 'C', 'D'];
      let letter = letters[index] || 'A';
      let text = opt;

      // Check if option text already starts with "A)" or "A." or "A:"
      const match = opt.match(/^([A-D])[\)\.\:\s]+(.*)$/i);
      if (match) {
        letter = match[1].toUpperCase();
        text = match[2];
      }

      let btnClass = 'option-btn';
      if (isGraded) {
        const isThisSelected = subLetter === letter || subLetter === text.trim().toUpperCase();
        const isThisCorrect = correctLetter === letter || correctLetter === text.trim().toUpperCase();

        if (isThisSelected && isCorrect) {
          btnClass += ' selected-correct';
        } else if (isThisSelected && !isCorrect) {
          btnClass += ' selected-incorrect';
        } else if (isThisCorrect) {
          btnClass += ' reveal-correct';
        }
      }

      const disabledAttr = isGraded ? 'disabled' : '';

      return `
        <button class="${btnClass}" data-letter="${letter}" data-text="${encodeURIComponent(text)}" ${disabledAttr} onclick="window.handleSelectOption('${letter}', this)">
          <div class="option-letter">${letter}</div>
          <div class="option-text">${text}</div>
        </button>
      `;
    }).join('');

    let gradingBanner = '';
    if (isGraded) {
      if (isCorrect) {
        gradingBanner = `
          <div class="grading-result-badge correct">
            <div class="grading-text">🎉 <strong>Correct Answer!</strong> Well done.</div>
            <div class="mastery-change-tag plus">+22% Mastery</div>
          </div>
        `;
      } else {
        gradingBanner = `
          <div class="grading-result-badge incorrect">
            <div class="grading-text">❌ <strong>Incorrect.</strong> Correct answer was Option ${correctLetter}.</div>
            <div class="mastery-change-tag minus">-8% Mastery</div>
          </div>
        `;
      }
    }

    return `
      <div class="practice-card" data-topic="${topic}">
        <div class="practice-header">
          <div class="practice-badge-group">
            <span class="badge-topic">📚 ${topic}</span>
            <span class="badge-difficulty ${difficulty}">${qData.difficulty || 'Medium'}</span>
          </div>
          <span style="font-size: 11px; color: var(--text-muted); font-weight: 500;">Practice Question</span>
        </div>
        <div class="practice-question-text">${qData.question}</div>
        <div class="practice-options-grid">
          ${optionsHtml}
        </div>
        ${gradingBanner}
      </div>
    `;
  },

  /**
   * Render a complete chat message (user or assistant)
   * @param {Object} msg - Message object
   * @returns {string} HTML string
   */
  renderChatMessage(msg) {
    const isUser = msg.role === 'user';
    const agentKey = msg.action || 'TEACH';
    const agentInfo = CONFIG.AGENTS[agentKey] || CONFIG.AGENTS.UNKNOWN;
    const timeStr = new Date(msg.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    let practiceCardHtml = '';
    if (msg.questionData) {
      practiceCardHtml = this.renderPracticeCard(
        msg.questionData,
        msg.isGraded || false,
        msg.submittedAnswer || null,
        msg.isCorrect
      );
    }

    let diagnosticCardHtml = '';
    if (msg.diagnosticData) {
      diagnosticCardHtml = `
        <div style="margin-top: 10px; background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.3); border-radius: var(--border-radius-md); padding: 14px;">
          <div style="font-weight: 700; color: var(--secondary-light); margin-bottom: 6px;">🩺 Diagnostic Assessment Ready</div>
          <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 10px;">The Diagnostic Agent generated a 5-topic evaluation to measure your baseline mastery.</p>
          <button class="btn-primary" style="width: auto; padding: 8px 16px; font-size: 13px;" onclick="window.openDiagnosticModal()">
            Launch Interactive Diagnostic Quiz →
          </button>
        </div>
      `;
    }

    const contentHtml = isUser
      ? `<div class="message-bubble">${msg.content}</div>`
      : `
        <div class="message-bubble">
          ${this.formatMarkdown(msg.content)}
          ${practiceCardHtml}
          ${diagnosticCardHtml}
        </div>
      `;

    const metaHtml = isUser
      ? `<span class="message-time">${timeStr}</span> <span class="message-author">You</span>`
      : `
        <span class="message-agent-tag">${agentInfo.icon} ${agentInfo.name}</span>
        ${msg.topic ? `<span class="message-topic-tag" style="font-size: 10px; color: var(--text-muted);">• ${msg.topic}</span>` : ''}
        <span class="message-time">• ${timeStr}</span>
      `;

    return `
      <div class="chat-message ${isUser ? 'user' : 'assistant'}" id="${msg.id}">
        <div class="chat-avatar">${isUser ? '👤' : agentInfo.icon}</div>
        <div class="message-content-wrapper">
          <div class="message-meta">${metaHtml}</div>
          ${contentHtml}
        </div>
      </div>
    `;
  },

  /**
   * Render Sidebar Topic Mastery Cards
   * @param {Object} masteryMap - Map of topic names to scores (0-100)
   * @param {string} selectedTopic - Active topic
   * @returns {string} HTML string
   */
  renderMasteryList(masteryMap, selectedTopic) {
    return CONFIG.TOPICS.map(topic => {
      const score = masteryMap[topic.name] !== undefined ? masteryMap[topic.name] : topic.defaultMastery;
      
      let statusClass = 'developing';
      let statusText = 'Developing';
      if (score < 50) {
        statusClass = 'weak';
        statusText = 'Weak';
      } else if (score >= 80) {
        statusClass = 'strong';
        statusText = 'Strong';
      }

      const isActive = (selectedTopic && selectedTopic.toLowerCase() === topic.name.toLowerCase());

      return `
        <div class="topic-mastery-card ${isActive ? 'active' : ''}" onclick="window.selectTopic('${topic.name}')">
          <div class="topic-header">
            <span class="topic-name">${topic.icon} ${topic.name}</span>
            <span class="topic-score ${statusClass}">${score}%</span>
          </div>
          <div class="mastery-progress-bar">
            <div class="mastery-fill ${statusClass}" style="width: ${score}%"></div>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="topic-badge-status ${statusClass}" style="color: var(--text-muted); font-size: 10.5px;">${statusText}</span>
            <span style="font-size: 10px; color: var(--primary-light);">Teach →</span>
          </div>
        </div>
      `;
    }).join('');
  }
};

window.RenderEngine = RenderEngine;
