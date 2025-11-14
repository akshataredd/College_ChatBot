"""
Chatbot Logic Module
Handles response generation, entity extraction, and context management
"""

import json
import os
import re
import random
from rapidfuzz import fuzz, process
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.intent_classifier import IntentClassifier

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')


class Chatbot:
    def __init__(self):
        self.classifier = IntentClassifier()
        self.classifier.load_model()
        self.college_info = self.load_json('college_info.json')
        self.courses = self.load_json('courses.json')
        self.faculty = self.load_json('faculty.json')
        self.events = self.load_json('events.json')
        self.context = []
        self.max_context = 5
        
    def load_json(self, filename):
        """Load JSON data file"""
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_entities(self, text):
        """
        Extract entities like department names, semester numbers, etc.
        
        Args:
            text (str): User input
            
        Returns:
            dict: Extracted entities
        """
        entities = {
            'department': None,
            'semester': None,
            'faculty_name': None
        }
        
        text_lower = text.lower()
        
        # Extract semester number
        sem_match = re.search(r'\b(semester|sem)\s*(\d+)\b', text_lower)
        if sem_match:
            entities['semester'] = sem_match.group(2)
        else:
            # Look for standalone numbers that might be semesters (1-8)
            num_match = re.search(r'\b([1-8])\b', text_lower)
            if num_match:
                entities['semester'] = num_match.group(1)
        
        # Extract department using fuzzy matching
        dept_names = list(self.courses.keys())
        if dept_names:
            match = process.extractOne(
                text_lower, 
                [d.lower() for d in dept_names], 
                scorer=fuzz.token_sort_ratio
            )
            if match and match[1] > 60:  # confidence threshold
                idx = [d.lower() for d in dept_names].index(match[0])
                entities['department'] = dept_names[idx]
        
        # Extract faculty name
        all_faculty = self.faculty.get('faculty', [])
        if 'principal' in text_lower and 'principal' in self.faculty:
            entities['faculty_name'] = 'principal'
        else:
            for f in all_faculty:
                name_parts = f['name'].lower().split()
                if any(part in text_lower for part in name_parts):
                    entities['faculty_name'] = f['name']
                    break
        
        return entities
    
    def get_response(self, user_input):
        """
        Generate response based on user input
        
        Args:
            user_input (str): User's question
            
        Returns:
            str: Bot's response
        """
        text_lower = user_input.lower()
        
        # Intent patterns with fuzzy matching
        intent_patterns = {
            'greeting': 'hi hello hey good morning afternoon evening namaste greetings',
            'goodbye': 'bye goodbye see you later exit quit',
            'thanks': 'thank thanks appreciate grateful',
            'college_timings': 'college timing time hour schedule open close start working office',
            'departments': 'department branch stream engineering course program',
            'facilities': 'facility infrastructure campus amenity building',
            'library': 'library book digital elib reading room journal',
            'hostel': 'hostel accommodation residence stay room warden mess',
            'transport': 'transport bus shuttle vehicle route pickup',
            'contact': 'contact phone email address reach location where find',
            'courses': 'course subject syllabus curriculum semester sem topic taught',
            'admission': 'admission apply enroll eligibility requirement join entry',
            'fees': 'fee cost price tuition payment installment money',
            'scholarship': 'scholarship financial aid concession waiver free education loan',
            'placements': 'placement job recruit package salary company career opportunity',
            'internship': 'internship training industrial project summer',
            'faculty': 'faculty teacher professor staff lecturer instructor',
            'principal': 'principal director head dean chief',
            'events': 'event fest festival workshop seminar conference holiday program',
            'sports': 'sport game gym cricket football basketball athletic fitness',
            'clubs': 'club society activity extracurricular cultural technical',
            'exams': 'exam test assessment evaluation result grade mark',
            'attendance': 'attendance present absent leave percentage minimum',
            'canteen': 'canteen cafeteria food mess lunch breakfast snack',
            'labs': 'lab laboratory workshop practical equipment computer',
            'alumni': 'alumni graduate past student network association'
        }
        
        # Use fuzzy matching on entire query against all intent patterns
        best_match = None
        best_score = 0
        
        for intent, pattern in intent_patterns.items():
            score = fuzz.partial_ratio(text_lower, pattern)
            # Also check token-based similarity
            token_score = fuzz.token_set_ratio(text_lower, pattern)
            final_score = max(score, token_score)
            
            if final_score > best_score:
                best_score = final_score
                best_match = intent
        
        # Use the best match if confidence is high enough
        intent_tag = None
        if best_score > 60:  # 60% similarity threshold
            intent_tag = best_match
        
        # If still no match, use ML classifier as fallback
        if not intent_tag:
            result = self.classifier.predict(user_input)
            intent_tag = result['tag']
            confidence = result['confidence']
            
            if confidence < 0.25:
                return self._fallback_response()
        
        # Extract entities
        entities = self.extract_entities(user_input)
        
        # Update context
        self.context.append({
            'input': user_input,
            'intent': intent_tag,
            'entities': entities
        })
        if len(self.context) > self.max_context:
            self.context = self.context[-self.max_context:]
        
        # Get fixed responses from intents.json
        intent_data = None
        for intent in self.classifier.intents:
            if intent['tag'] == intent_tag:
                intent_data = intent
                break
        
        # Generate response
        response = self._generate_intent_response(intent_tag, entities, intent_data)
        
        return response
    
    def _generate_intent_response(self, intent_tag, entities, intent_data):
        """Generate response based on intent and extracted entities"""
        
        # Intents with fixed responses
        if intent_data and intent_data.get('responses'):
            return random.choice(intent_data['responses'])
        
        # Dynamic responses based on data
        if intent_tag == 'college_timings':
            return self._format_response(
                "🕒 College Timings",
                self.college_info.get('timings', 'Timings not available')
            )
        
        elif intent_tag == 'departments':
            depts = self.college_info.get('departments', [])
            return self._format_list_response("📚 Departments", depts)
        
        elif intent_tag == 'facilities':
            facilities = self.college_info.get('facilities', [])
            return self._format_list_response("🏫 Campus Facilities", facilities)
        
        elif intent_tag == 'library':
            library = self.college_info.get('library', {})
            return f"📚 Library Facilities:\n\n" \
                   f"Timings: {library.get('timings', 'N/A')}\n" \
                   f"Books: {library.get('books', 'N/A')}\n" \
                   f"Digital Library: {library.get('digital', 'Available')}\n" \
                   f"Reading Room: {library.get('reading_room', 'Available')}"
        
        elif intent_tag == 'hostel':
            hostel = self.college_info.get('hostel', {})
            return f"🏠 Hostel Facilities:\n\n" \
                   f"Available: {hostel.get('available', 'Yes')}\n" \
                   f"Boys Hostel: {hostel.get('boys', 'Available')}\n" \
                   f"Girls Hostel: {hostel.get('girls', 'Available')}\n" \
                   f"Fees: {hostel.get('fees', 'Contact hostel office')}\n" \
                   f"Contact: {hostel.get('contact', 'N/A')}"
        
        elif intent_tag == 'transport':
            transport = self.college_info.get('transport', {})
            return f"🚌 Transport Facilities:\n\n" \
                   f"Bus Service: {transport.get('available', 'Available')}\n" \
                   f"Routes: {transport.get('routes', 'Multiple routes available')}\n" \
                   f"Timings: {transport.get('timings', 'Contact transport office')}\n" \
                   f"Fees: {transport.get('fees', 'N/A')}"
        
        elif intent_tag == 'contact':
            contact = self.college_info.get('contact', {})
            address = self.college_info.get('address', 'N/A')
            return f"📞 Contact Information:\n\n" \
                   f"Phone: {contact.get('phone', 'N/A')}\n" \
                   f"Email: {contact.get('email', 'N/A')}\n" \
                   f"Address: {address}\n" \
                   f"Website: {self.college_info.get('website', 'N/A')}"
        
        elif intent_tag == 'courses':
            return self._handle_courses(entities)
        
        elif intent_tag == 'admission':
            admission = self.college_info.get('admission', {})
            return f"🎓 Admissions Information:\n\n" \
                   f"Status: {admission.get('status', 'Open')}\n" \
                   f"Last Date: {admission.get('last_date', 'Check website')}\n" \
                   f"Eligibility: {admission.get('eligibility', 'Check department wise')}\n" \
                   f"📧 Contact: {admission.get('email', 'admissions@college.edu')}\n" \
                   f"📞 Phone: {admission.get('phone', 'Contact admission office')}"
        
        elif intent_tag == 'fees':
            return self._handle_fees(entities)
        
        elif intent_tag == 'scholarship':
            scholarship = self.college_info.get('scholarship', {})
            return f"💰 Scholarship Information:\n\n" \
                   f"Merit Scholarship: {scholarship.get('merit', 'Available')}\n" \
                   f"Financial Aid: {scholarship.get('financial_aid', 'Available for eligible students')}\n" \
                   f"Government Schemes: {scholarship.get('government', 'Available')}\n" \
                   f"Contact: {scholarship.get('contact', 'Scholarship cell')}"
        
        elif intent_tag == 'placements':
            placements = self.college_info.get('placements', {})
            return f"💼 Placement Statistics:\n\n" \
                   f"Placement %: {placements.get('percentage', 'N/A')}\n" \
                   f"Highest Package: {placements.get('highest', 'N/A')}\n" \
                   f"Average Package: {placements.get('average', 'N/A')}\n" \
                   f"Top Recruiters: {placements.get('companies', 'Multiple companies visit')}\n" \
                   f"Contact: {placements.get('contact', 'Placement cell')}"
        
        elif intent_tag == 'internship':
            internship = self.college_info.get('internship', {})
            return f"🎯 Internship Opportunities:\n\n" \
                   f"Available: {internship.get('available', 'Yes')}\n" \
                   f"Duration: {internship.get('duration', '6-8 weeks')}\n" \
                   f"Type: {internship.get('type', 'Industry internships available')}\n" \
                   f"Contact: {internship.get('contact', 'Training & Placement cell')}"
        
        elif intent_tag == 'faculty' or intent_tag == 'principal':
            return self._handle_faculty(entities)
        
        elif intent_tag == 'events':
            return self._handle_events()
        
        elif intent_tag == 'sports':
            sports = self.college_info.get('sports', {})
            sports_list = sports.get('available', [])
            return self._format_list_response("⚽ Sports Facilities", sports_list)
        
        elif intent_tag == 'clubs':
            clubs = self.college_info.get('clubs', {})
            clubs_list = clubs.get('available', [])
            return self._format_list_response("🎭 Student Clubs", clubs_list)
        
        elif intent_tag == 'exams':
            exams = self.college_info.get('exams', {})
            return f"📝 Examination Information:\n\n" \
                   f"Pattern: {exams.get('pattern', 'Semester system')}\n" \
                   f"Internal: {exams.get('internal', 'Regular assessments')}\n" \
                   f"Semester Exams: {exams.get('semester', 'As per university schedule')}\n" \
                   f"Results: {exams.get('results', 'Published on college website')}"
        
        elif intent_tag == 'attendance':
            attendance = self.college_info.get('attendance', {})
            return f"📊 Attendance Policy:\n\n" \
                   f"Minimum Required: {attendance.get('minimum', '75%')}\n" \
                   f"Policy: {attendance.get('policy', 'Mandatory as per university norms')}\n" \
                   f"Concession: {attendance.get('concession', 'Medical certificates accepted')}"
        
        elif intent_tag == 'canteen':
            canteen = self.college_info.get('canteen', {})
            return f"🍽️ Canteen Facilities:\n\n" \
                   f"Available: {canteen.get('available', 'Yes')}\n" \
                   f"Timings: {canteen.get('timings', '8 AM - 5 PM')}\n" \
                   f"Menu: {canteen.get('menu', 'Breakfast, lunch, snacks available')}"
        
        elif intent_tag == 'labs':
            labs = self.college_info.get('labs', {})
            labs_list = labs.get('available', [])
            return self._format_list_response("🔬 Laboratory Facilities", labs_list)
        
        elif intent_tag == 'alumni':
            alumni = self.college_info.get('alumni', {})
            return f"👥 Alumni Network:\n\n" \
                   f"Network: {alumni.get('network', 'Active alumni association')}\n" \
                   f"Portal: {alumni.get('portal', 'Available')}\n" \
                   f"Contact: {alumni.get('contact', 'alumni@college.edu')}"
        
        else:
            return self._fallback_response()
    
    def _handle_courses(self, entities):
        """Handle course-related queries"""
        dept = entities.get('department')
        sem = entities.get('semester')
        
        if not dept:
            # List all departments
            depts = ', '.join(self.courses.keys())
            return f"📖 Available Departments:\n\n{depts}\n\n" \
                   "Please specify a department to see course details."
        
        if dept not in self.courses:
            return f"Sorry, I don't have information about {dept}. " \
                   f"Available departments: {', '.join(self.courses.keys())}"
        
        dept_data = self.courses[dept]
        
        if sem and sem in dept_data.get('semesters', {}):
            subjects = dept_data['semesters'][sem]
            return self._format_list_response(
                f"📖 {dept} - Semester {sem}",
                subjects
            )
        else:
            sems = ', '.join(dept_data.get('semesters', {}).keys())
            fees = dept_data.get('fees', 'N/A')
            return f"📖 {dept}\n\n" \
                   f"Available Semesters: {sems}\n" \
                   f"💰 Fees: {fees}\n\n" \
                   "Please specify a semester number (e.g., 'semester 1')"
    
    def _handle_fees(self, entities):
        """Handle fee-related queries"""
        dept = entities.get('department')
        
        if dept and dept in self.courses:
            fees = self.courses[dept].get('fees', 'N/A')
            return f"💰 {dept} Fees:\n\n{fees}"
        else:
            # Show all fees
            fee_list = []
            for dept, data in self.courses.items():
                fee_list.append(f"{dept}: {data.get('fees', 'N/A')}")
            return self._format_list_response("💰 Fee Structure", fee_list)
    
    def _handle_faculty(self, entities):
        """Handle faculty-related queries"""
        faculty_name = entities.get('faculty_name')
        
        if faculty_name == 'principal' and 'principal' in self.faculty:
            p = self.faculty['principal']
            return f"👤 Principal\n\n" \
                   f"Name: {p.get('name', 'N/A')}\n" \
                   f"Qualifications: {p.get('qualifications', 'N/A')}\n" \
                   f"📧 Email: {p.get('email', 'N/A')}"
        
        elif faculty_name:
            # Find specific faculty
            for f in self.faculty.get('faculty', []):
                if f['name'] == faculty_name:
                    return f"👤 {f['name']}\n\n" \
                           f"Designation: {f['designation']}\n" \
                           f"Department: {f['dept']}"
        
        # List all faculty
        faculty_list = []
        for f in self.faculty.get('faculty', [])[:10]:  # Limit to 10
            faculty_list.append(f"{f['name']} - {f['designation']}")
        
        return self._format_list_response("👥 Faculty Members", faculty_list)
    
    def _handle_events(self):
        """Handle event-related queries"""
        upcoming = self.events.get('upcoming', [])
        
        if not upcoming:
            return "📅 No upcoming events at the moment. Check back later!"
        
        event_list = []
        for e in upcoming:
            event_list.append(
                f"{e['title']} - {e['date']} at {e.get('location', 'TBA')}"
            )
        
        return self._format_list_response("📅 Upcoming Events", event_list)
    
    def _format_response(self, title, content):
        """Format a simple response with title"""
        return f"{title}\n\n{content}"
    
    def _format_list_response(self, title, items):
        """Format a list response with bullets"""
        if not items:
            return f"{title}\n\nNo items available."
        
        formatted = '\n'.join([f"• {item}" for item in items])
        return f"{title}\n\n{formatted}"
    
    def _fallback_response(self):
        """Generate fallback response when intent is unclear"""
        responses = [
            "I'm not sure I understand. Could you rephrase that?",
            "Sorry, I didn't quite get that. I can help with:\n• College timings\n• Courses and fees\n• Admissions\n• Faculty and departments\n• Events",
            "I'm here to help with college information. Try asking about courses, admissions, faculty, or events!"
        ]
        return random.choice(responses)
    
    def clear_context(self):
        """Clear conversation context"""
        self.context = []


if __name__ == '__main__':
    # Test the chatbot
    print("=" * 60)
    print("CHATBOT TEST")
    print("=" * 60 + "\n")
    
    bot = Chatbot()
    
    test_queries = [
        "Hello!",
        "What are the college timings?",
        "Tell me about Computer Science courses",
        "What subjects are there in semester 3?",
        "Who is the principal?",
        "What facilities do you have?"
    ]
    
    for query in test_queries:
        print(f"You: {query}")
        response = bot.get_response(query)
        print(f"Bot: {response}\n")
