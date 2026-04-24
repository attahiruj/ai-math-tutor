import { useState, useEffect, useRef } from 'react'
import { APIClient } from './api'
import WelcomeScreen from './components/WelcomeScreen'
import ProfileScreen from './components/ProfileScreen'
import ActivityScreen from './components/ActivityScreen'
import FeedbackScreen from './components/FeedbackScreen'
import ReportScreen from './components/ReportScreen'

export default function App() {
  const [screen, setScreen] = useState('welcome')
  const [lang, setLang] = useState('EN')
  const [learner, setLearner] = useState(null)
  const [studentId, setStudentId] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [currentItem, setCurrentItem] = useState(null)
  const [feedbackText, setFeedbackText] = useState('')
  const [questionIdx, setQuestionIdx] = useState(0)
  const [correct, setCorrect] = useState(false)
  const [streak, setStreak] = useState(0)
  const [silenceTimer, setSilenceTimer] = useState(10)

  const apiRef = useRef(new APIClient())

  useEffect(() => {
    if (screen !== 'activity') return
    setSilenceTimer(10)
    const id = setInterval(() => {
      setSilenceTimer((t) => {
        if (t <= 1) { clearInterval(id); return 0 }
        return t - 1
      })
    }, 1000)
    return () => clearInterval(id)
  }, [screen, questionIdx])

  const loadNextItem = async (sid) => {
    try {
      const item = await apiRef.current.getNextItem(sid, lang.toLowerCase())
      setCurrentItem(item)
      setQuestionIdx((prev) => prev + 1)
    } catch (err) {
      console.error('Failed to load item:', err)
    }
  }

  const handleProfileSelect = (profile) => {
    if (!profile) return
    setLearner(profile)
    setStudentId(profile.student_id)
    setSessionId(profile.session_id)
    setScreen('activity')
    loadNextItem(profile.student_id)
  }

  const handleAnswer = async (choice) => {
    if (!currentItem) return
    try {
      const result = await apiRef.current.submitTap(studentId, sessionId, currentItem.id, choice)
      setCorrect(result.correct)
      setFeedbackText(result.feedback_text)
      setStreak((prev) => (result.correct ? prev + 1 : 0))
      setScreen('feedback')
    } catch (err) {
      console.error('Failed to submit answer:', err)
    }
  }

  const handleFeedbackNext = () => {
    setScreen('activity')
    loadNextItem(studentId)
  }

  switch (screen) {
    case 'welcome':
      return <WelcomeScreen lang={lang} setLang={setLang} onNext={() => setScreen('profile')} />
    case 'profile':
      return <ProfileScreen lang={lang} onSelect={handleProfileSelect} api={apiRef.current} />
    case 'activity':
      return currentItem
        ? <ActivityScreen
            lang={lang} learner={learner} item={currentItem} onAnswer={handleAnswer}
            questionIdx={questionIdx} silenceCountdown={silenceTimer} api={apiRef.current}
          />
        : <div className="screen">Loading...</div>
    case 'feedback':
      return <FeedbackScreen
        lang={lang} correct={correct} feedbackText={feedbackText} streak={streak}
        onNext={handleFeedbackNext} onParent={() => setScreen('report')}
      />
    case 'report':
      return <ReportScreen lang={lang} learner={learner} onBack={() => setScreen('activity')} api={apiRef.current} />
    default:
      return <div>Unknown screen</div>
  }
}
