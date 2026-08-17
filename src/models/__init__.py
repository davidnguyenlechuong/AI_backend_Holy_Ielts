from src.models.auth import User, AuthAccount, RefreshToken, EmailVerificationToken, PasswordResetToken
from src.models.ielts import Test, TestSection, Passage, Question, QuestionOption, TestAttempt, TestAttemptAnswer
from src.models.submissions import Submission, GradingResult, GradingCriteriaScore, SpeakingAnalysis
from src.models.vocabulary import Vocabulary, UserVocabulary, SubmissionVocabulary
from src.models.progress import UserSkillProgress, BandScoreHistory
from src.models.payments import Order

# Export all models so alembic can pick them up from src.db.base.Base
__all__ = [
    "User", "AuthAccount", "RefreshToken", "EmailVerificationToken", "PasswordResetToken",
    "Test", "TestSection", "Passage", "Question", "QuestionOption", "TestAttempt", "TestAttemptAnswer",
    "Submission", "GradingResult", "GradingCriteriaScore", "SpeakingAnalysis",
    "Vocabulary", "UserVocabulary", "SubmissionVocabulary",
    "UserSkillProgress", "BandScoreHistory",
    "Order",
]
