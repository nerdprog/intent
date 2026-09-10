const ApiClient = {
  /**
   * Send a student message or grading payload to the agent backend
   */
  async sendMessage({ student_id, message, topic, mastery, answer, correct_answer }) {
    const payload = {
      student_id: student_id || 'student_demo_01',
      message: (message || '').trim()
    };

    if (topic) payload.topic = topic;
    if (typeof mastery === 'number' && !isNaN(mastery)) payload.mastery = mastery;
    if (answer) payload.answer = answer;
    if (correct_answer) payload.correct_answer = correct_answer;

    console.log('[StudyCrafter API] Sending payload:', payload);

    // List of endpoints to try: Local Python Multi-Agent API first, then local proxy, then remote n8n
    const endpoints = [
      '/api/agent',
      '/api/webhook',
      CONFIG.WEBHOOK_URL
    ];

    let lastError = null;

    for (const endpoint of endpoints) {
      try {
        console.log(`[StudyCrafter API] Attempting POST to: ${endpoint}`);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT || 20000);

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(payload),
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Endpoint ${endpoint} returned status ${response.status}: ${errorText || response.statusText}`);
        }

        const data = await response.json();
        console.log('[StudyCrafter API] Received response:', data);

        // Normalize question payload if present
        let agentOut = data.agent_output || {};
        if (data.question && !agentOut.question) {
          const q = data.question;
          agentOut = {
            question: q.question || q.text,
            options: Array.isArray(q.options) ? q.options : Object.entries(q.options || {}).map(([k, v]) => `${k}) ${v}`),
            correct_answer: q.correct_answer,
            difficulty: q.difficulty || 'Medium',
            topic: q.topic || data.topic
          };
        }

        return {
          ok: data.ok !== undefined ? data.ok : true,
          action: data.action || 'TEACH',
          topic: data.topic || topic || null,
          response: data.response || (typeof data.agent_output === 'string' ? data.agent_output : ''),
          agent_output: agentOut,
          student_state: data.student_state || {}
        };
      } catch (err) {
        console.warn(`[StudyCrafter API] Failed for ${endpoint}:`, err);
        lastError = err;
      }
    }

    // Fallback engine if backend is unreachable
    console.warn('[StudyCrafter API] Backend endpoints unreachable. Using dynamic local fallback.');
    return this.fallbackEngine({ student_id, message, topic, mastery, answer, correct_answer });
  },

  // Track served fallback question indices
  _servedIndices: {},

  /**
   * Dynamic local fallback engine with anti-repetition and direct doubt explanations
   */
  fallbackEngine({ student_id, message, topic, mastery, answer, correct_answer }) {
    const text = (message || '').trim().toLowerCase();
    const currentMastery = typeof mastery === 'number' ? mastery : 40;

    let activeTopic = topic || 'Probability';
    const knownTopics = [
      'Percentages',
      'Ratio and Proportion',
      'Averages',
      'Time and Work',
      'Time Speed and Distance',
      'Profit and Loss',
      'Probability'
    ];
    for (const t of knownTopics) {
      if (text.includes(t.toLowerCase()) || text.includes(t.split(' ')[0].toLowerCase())) {
        activeTopic = t;
        break;
      }
    }

    // 1. Grading mode
    if (answer && correct_answer) {
      const sub = answer.trim().toUpperCase();
      const cor = correct_answer.trim().toUpperCase();
      const isCorrect = sub === cor;
      return {
        ok: true,
        action: 'ASSESS',
        topic: activeTopic,
        response: `Answer evaluated: **${isCorrect ? 'Correct 🎉' : 'Incorrect ❌'}** for ${activeTopic}.\n\n` +
          (isCorrect 
            ? `Great job! Your approach was correct. Ready for the next problem?` 
            : `The correct option was **${cor}**. Pay close attention to the formula step!`),
        agent_output: {
          student_id,
          topic: activeTopic,
          submitted_answer: sub,
          correct_answer: cor,
          correct: isCorrect
        },
        student_state: {
          student_id,
          last_action: 'ASSESS',
          last_topic: activeTopic,
          last_mastery: isCorrect ? Math.min(100, currentMastery + 22) : Math.max(0, currentMastery - 8)
        }
      };
    }

    // 2. Multi-Question Pool for Anti-Repetition
    const questionPool = {
      'Percentages': [
        { q: 'A shirt priced at $80 is discounted by 25%. What is the final sale price?', options: ['A) $55', 'B) $60', 'C) $65', 'D) $70'], correct: 'B', diff: 'Easy' },
        { q: 'What is 15% of 240?', options: ['A) 32', 'B) 36', 'C) 40', 'D) 48'], correct: 'B', diff: 'Easy' },
        { q: 'In a class of 50 students, 60% are girls. How many boys are in the class?', options: ['A) 15', 'B) 20', 'C) 25', 'D) 30'], correct: 'B', diff: 'Easy' },
        { q: 'If 40% of a number is equal to 120, what is 15% of that same number?', options: ['A) 35', 'B) 45', 'C) 50', 'D) 60'], correct: 'B', diff: 'Medium' }
      ],
      'Ratio and Proportion': [
        { q: 'Divide $5,000 between A and B in the ratio 2:3. How much does person A receive?', options: ['A) $1,500', 'B) $2,000', 'C) $2,500', 'D) $3,000'], correct: 'B', diff: 'Easy' },
        { q: 'The ratio of boys to girls in a club is 5:4. If there are 36 girls, how many boys are there?', options: ['A) 40', 'B) 45', 'C) 50', 'D) 54'], correct: 'B', diff: 'Easy' },
        { q: 'If A:B = 3:4 and B:C = 8:9, find A:C.', options: ['A) 2:3', 'B) 3:2', 'C) 1:2', 'D) 3:4'], correct: 'A', diff: 'Medium' }
      ],
      'Averages': [
        { q: 'The average of 5 numbers is 18. Four of the numbers sum to 70. What is the fifth number?', options: ['A) 18', 'B) 20', 'C) 22', 'D) 25'], correct: 'B', diff: 'Easy' },
        { q: 'Find the average of 10, 20, 30, 40, and 50.', options: ['A) 25', 'B) 30', 'C) 35', 'D) 40'], correct: 'B', diff: 'Easy' }
      ],
      'Time and Work': [
        { q: 'Person A completes a job in 10 days and Person B in 15 days. Working together, how many days will they take?', options: ['A) 5 days', 'B) 6 days', 'C) 7.5 days', 'D) 8 days'], correct: 'B', diff: 'Easy' },
        { q: 'Pipe A fills a tank in 8 hours and Pipe B empties it in 12 hours. If both are opened together, in how many hours is it full?', options: ['A) 16 hours', 'B) 20 hours', 'C) 24 hours', 'D) 30 hours'], correct: 'C', diff: 'Medium' }
      ],
      'Time Speed and Distance': [
        { q: 'A car travels a distance of 150 km in 3 hours. What is its average speed in km/h?', options: ['A) 45 km/h', 'B) 50 km/h', 'C) 55 km/h', 'D) 60 km/h'], correct: 'B', diff: 'Easy' },
        { q: 'Convert a speed of 72 km/h into meters per second (m/s).', options: ['A) 15 m/s', 'B) 20 m/s', 'C) 25 m/s', 'D) 30 m/s'], correct: 'B', diff: 'Easy' }
      ],
      'Profit and Loss': [
        { q: 'An item bought for $500 is sold for $600. What is the profit percentage?', options: ['A) 15%', 'B) 20%', 'C) 25%', 'D) 30%'], correct: 'B', diff: 'Easy' },
        { q: 'Cost Price = $800, Profit = 10%. What is the Selling Price?', options: ['A) $850', 'B) $880', 'C) $900', 'D) $920'], correct: 'B', diff: 'Easy' }
      ],
      'Probability': [
        { q: 'A bag contains 3 red balls and 2 blue balls. If one ball is drawn at random, what is the probability of drawing a red ball?', options: ['A) 2/5', 'B) 3/5', 'C) 1/2', 'D) 3/2'], correct: 'B', diff: 'Easy' },
        { q: 'A fair six-sided die is rolled once. What is the probability of getting an even number?', options: ['A) 1/3', 'B) 1/2', 'C) 2/3', 'D) 1/6'], correct: 'B', diff: 'Easy' },
        { q: 'Two fair dice are rolled. What is the probability that the sum equals 8?', options: ['A) 5/36', 'B) 1/6', 'C) 7/36', 'D) 1/9'], correct: 'A', diff: 'Hard' }
      ]
    };

    const isQuestionRequest = text.includes('practice') || text.includes('question') || text.includes('quiz') || text.includes('test me') || text.includes('problem');

    if (isQuestionRequest) {
      const list = questionPool[activeTopic] || questionPool['Probability'];
      const lastIdx = this._servedIndices[activeTopic] !== undefined ? this._servedIndices[activeTopic] : -1;
      const nextIdx = (lastIdx + 1) % list.length;
      this._servedIndices[activeTopic] = nextIdx;
      const item = list[nextIdx];

      return {
        ok: true,
        action: 'PRACTICE',
        topic: activeTopic,
        response: `Here is a practice question on **${activeTopic}** to test your knowledge:`,
        agent_output: {
          output: {
            question: item.q,
            options: item.options,
            correct_answer: item.correct,
            difficulty: item.diff,
            topic: activeTopic
          }
        },
        student_state: {
          student_id,
          last_action: 'PRACTICE',
          last_topic: activeTopic,
          last_mastery: currentMastery
        }
      };
    }

    // 3. Direct query/doubt response
    return {
      ok: true,
      action: 'TEACH',
      topic: activeTopic,
      response: `### 📚 ${activeTopic}\n\n` +
        `**Key Concept:**\nMastering **${activeTopic}** involves understanding the fundamental ratio and rate formulas. Focus on identifying given quantities and setting up the equation cleanly.\n\n` +
        `**Pro Tip:** Look for common cancellation factors or mental math fractions to solve under 45 seconds.\n\n` +
        `👉 *Ready to solve a problem? Click **"Practice Question"** or ask me any specific question!*`,
      agent_output: {},
      student_state: {
        student_id,
        last_action: 'TEACH',
        last_topic: activeTopic,
        last_mastery: currentMastery
      }
    };
  }
};

window.ApiClient = ApiClient;

