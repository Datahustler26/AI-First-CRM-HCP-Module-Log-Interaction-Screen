import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendChatMessage, clearChatHistory } from '../store/interactionSlice';
import { Send, Bot, User, RefreshCw, Trash2, ShieldAlert } from 'lucide-react';

export default function AIAssistant() {
  const dispatch = useDispatch();
  const { chatHistory, formDraft, isChatLoading } = useSelector(state => state.interactions);
  const [inputText, setInputText] = useState('');
  const chatEndRef = useRef(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isChatLoading]);

  // Send message handler
  const handleSend = () => {
    if (!inputText.trim() || isChatLoading) return;
    
    // Add user message to Redux first
    dispatch({
      type: 'interactions/addChatMessage',
      payload: { role: 'user', content: inputText }
    });

    // Send to LangGraph API
    dispatch(sendChatMessage({
      message: inputText,
      history: chatHistory,
      formDraft: formDraft
    }));

    setInputText('');
  };

  // Simple custom Markdown formatter for chat bubbles
  const renderMessageContent = (content) => {
    // Basic parser for lists, bolding, and newlines
    const lines = content.split('\n');
    return lines.map((line, i) => {
      let element = line;
      
      // Bullet items
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        const cleaned = line.replace(/^[-*]\s+/, '');
        element = (
          <li key={i} className="ml-4 list-disc text-slate-300 my-0.5">
            {parseBoldText(cleaned)}
          </li>
        );
      } else if (line.trim().startsWith('• ')) {
        const cleaned = line.replace(/^•\s+/, '');
        element = (
          <li key={i} className="ml-4 list-disc text-slate-300 my-0.5">
            {parseBoldText(cleaned)}
          </li>
        );
      } else if (/^\d+\.\s+/.test(line.trim())) {
        // Numbered list
        const cleaned = line.replace(/^\d+\.\s+/, '');
        element = (
          <li key={i} className="ml-4 list-decimal text-slate-300 my-0.5">
            {parseBoldText(cleaned)}
          </li>
        );
      } else {
        element = (
          <p key={i} className="my-1 text-slate-200">
            {parseBoldText(line)}
          </p>
        );
      }
      return element;
    });
  };

  const parseBoldText = (text) => {
    if (!text.includes('**')) return text;
    const parts = text.split('**');
    return parts.map((part, i) => i % 2 === 1 ? <strong key={i} className="text-white font-semibold">{part}</strong> : part);
  };

  return (
    <div className="glass-card p-6 flex flex-col h-[700px] relative overflow-hidden">
      {/* Subtle Glow */}
      <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-purple-500/10 rounded-full blur-3xl pointer-events-none"></div>

      {/* Header */}
      <div className="flex justify-between items-center pb-4 border-b border-white/10 mb-4 z-10">
        <h2 className="text-xl font-semibold flex items-center gap-2 text-white">
          <Bot className="text-purple-400 w-5 h-5" />
          AI Assistant
        </h2>
        <button
          onClick={() => dispatch(clearChatHistory())}
          className="text-xs p-1.5 rounded-full hover:bg-white/5 text-slate-400 hover:text-red-400 transition"
          title="Clear Conversation"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Chat Messages Log */}
      <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-4 mb-4 z-10 scrollbar-thin">
        {chatHistory.map((msg, index) => (
          <div
            key={index}
            className={`flex gap-3 max-w-[85%] ${
              msg.role === 'user' ? 'self-end flex-row-reverse' : 'self-start'
            }`}
          >
            {/* Avatar */}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 border ${
              msg.role === 'user'
                ? 'bg-purple-500/20 border-purple-500/30 text-purple-300'
                : 'bg-teal-500/20 border-teal-500/30 text-teal-300'
            }`}>
              {msg.role === 'user' ? <User className="w-4.5 h-4.5" /> : <Bot className="w-4.5 h-4.5" />}
            </div>

            {/* Bubble */}
            <div className={`p-3.5 rounded-2xl leading-relaxed text-sm ${
              msg.role === 'user'
                ? 'bg-purple-500/15 border border-purple-500/20 text-slate-200 rounded-tr-none'
                : 'bg-white/5 border border-white/10 text-slate-200 rounded-tl-none'
            }`}>
              {msg.role === 'assistant' ? (
                <ul className="list-inside">{renderMessageContent(msg.content)}</ul>
              ) : (
                <p className="text-slate-200">{msg.content}</p>
              )}
            </div>
          </div>
        ))}

        {/* Shimmering Typing Indicator */}
        {isChatLoading && (
          <div className="flex gap-3 self-start max-w-[85%]">
            <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-teal-500/20 border border-teal-500/30 text-teal-300">
              <Bot className="w-4.5 h-4.5" />
            </div>
            <div className="p-3.5 bg-white/5 border border-white/10 rounded-2xl rounded-tl-none flex items-center gap-1">
              <span className="w-2.5 h-2.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-2.5 h-2.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
              <span className="w-2.5 h-2.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input panel */}
      <div className="flex gap-2 mt-auto z-10 pt-4 border-t border-white/10">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Describe interaction..."
          className="input-field flex-1 text-sm bg-white/5 border-white/10 text-white rounded-xl focus:border-purple-500 focus:shadow-[0_0_8px_rgba(168,85,247,0.2)]"
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSend();
          }}
          disabled={isChatLoading}
        />
        <button
          onClick={handleSend}
          disabled={isChatLoading || !inputText.trim()}
          className="px-4 py-3 bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-purple-500/25 transition flex items-center gap-1.5"
        >
          {isChatLoading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Log</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
