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
        self.max_context = 10
        self.current_department = None
        
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
        
        # Extract semester number - multiple patterns
        # Pattern 1: "semester 1", "sem 1", "sem1"
        sem_match = re.search(r'\b(?:semester|sem)\s*(\d+)\b', text_lower)
        if sem_match:
            entities['semester'] = sem_match.group(1)
        # Pattern 2: standalone number (1-8)
        elif re.search(r'^\d+$', text_lower.strip()):
            # Just a number by itself
            num = text_lower.strip()
            if num in ['1', '2', '3', '4', '5', '6', '7', '8']:
                entities['semester'] = num
        # Pattern 3: number in text
        else:
            num_match = re.search(r'\b([1-8])(?:st|nd|rd|th)?\b', text_lower)
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
        
        # Reset department context if user asks generic questions
        reset_keywords = ['all courses', 'all programs', 'what courses', 'which courses', 
                         'available courses', 'available programs', 'show courses', 'list courses',
                         'show programs', 'list programs', 'tell me courses', 'tell me programs']
        if any(keyword in text_lower for keyword in reset_keywords) or text_lower.strip() in ['courses', 'programs', 'course', 'program']:
            self.current_department = None
        
        # Check if user is asking about a specific department/course or semester
        dept_keywords = ['cse', 'computer science', 'cs', 'ece', 'electronics', 'mechanical', 
                        'mech', 'civil', 'eee', 'electrical', 'it', 'information technology',
                        'mca', 'mba', 'master', 'b.tech', 'btech', 'engineering']
        
        sem_keywords = ['semester', 'sem', '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th',
                       'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth']
        
        is_dept_query = any(keyword in text_lower for keyword in dept_keywords)
        is_sem_query = any(keyword in text_lower for keyword in sem_keywords) or re.match(r'^\d+$', text_lower.strip())
        
        # Check if just a number and previous context was courses
        if re.match(r'^\d+$', text_lower.strip()) and self.context:
            for prev in reversed(self.context):
                if prev.get('intent') == 'courses':
                    is_sem_query = True
                    break
        
        # Intent patterns with fuzzy matching
        intent_patterns = {
            'greeting': 'hi hello hey good morning afternoon evening namaste greetings hola howdy',
            'goodbye': 'bye goodbye see you later exit quit thanks bye farewell',
            'thanks': 'thank thanks appreciate grateful thankyou',
            'college_timings': 'college timing time hour schedule open close start working office when does college',
            'departments': 'what which show list all available department branch stream how many departments tell me about departments',
            'facilities': 'facility infrastructure campus amenity building what facilities available campus facilities',
            'library': 'library book digital elib reading room journal library facility library timing',
            'hostel': 'hostel accommodation residence stay room warden mess hostel facility hostel fee',
            'transport': 'transport bus shuttle vehicle route pickup bus facility college bus',
            'contact': 'contact phone email address reach location where find contact details contact number',
            'courses': 'course subject syllabus curriculum semester sem topic taught program specialization',
            'admission': 'admission apply enroll eligibility requirement join entry how to apply admission process',
            'fees': 'fee cost price tuition payment installment money fee structure course fees',
            'scholarship': 'scholarship financial aid concession waiver free education loan scholarship available',
            'placements': 'placement job recruit package salary company career opportunity placement record companies visit',
            'internship': 'internship training industrial project summer internship opportunities',
            'faculty': 'faculty teacher professor staff lecturer instructor faculty details faculty members',
            'principal': 'principal director head dean chief who is principal',
            'events': 'event fest festival workshop seminar conference holiday program upcoming events',
            'sports': 'sport game gym cricket football basketball athletic fitness sports facility playground',
            'clubs': 'club society activity extracurricular cultural technical student clubs',
            'exams': 'exam test assessment evaluation result grade mark examination pattern exam schedule',
            'attendance': 'attendance present absent leave percentage minimum attendance required attendance policy',
            'canteen': 'canteen cafeteria food mess lunch breakfast snack canteen facility food available',
            'labs': 'lab laboratory workshop practical equipment computer lab facility laboratory equipment',
            'alumni': 'alumni graduate past student network association alumni network'
        }
        
        # If it's a department/semester query, force it to 'courses' intent
        if (is_dept_query or is_sem_query) and len(text_lower.split()) <= 5:  # Short queries
            intent_tag = 'courses'
            best_score = 100
        else:
            # Exact keyword matching first (higher priority)
            exact_matches = {
                'departments': ['departments', 'department', 'branches', 'branch'],
                'courses': ['courses', 'programs', 'what courses'],
                'events': ['events', 'event', 'fest', 'festival', 'workshop'],
                'placements': ['placements', 'placement', 'companies', 'package'],
                'hostel': ['hostel', 'accommodation', 'hostel facility'],
                'library': ['library', 'library facility', 'books'],
                'canteen': ['canteen', 'cafeteria', 'food'],
                'labs': ['lab', 'laboratory', 'computer lab'],
                'sports': ['sports', 'sport', 'gym', 'playground'],
                'facilities': ['facilities', 'infrastructure', 'campus'],
                'admission': ['admission', 'admissions', 'how to apply'],
                'contact': ['contact', 'phone', 'email', 'address']
            }
            
            intent_tag = None
            best_score = 0
            
            # Check exact matches first (but not for single digit queries)
            for intent, keywords in exact_matches.items():
                for keyword in keywords:
                    if keyword in text_lower and len(text_lower.split()) <= 3 and not re.match(r'^\d+$', text_lower.strip()):
                        intent_tag = intent
                        best_score = 100
                        break
                if intent_tag:
                    break
            
            # If no exact match, use fuzzy matching
            if not intent_tag:
                best_match = None
                
                for intent, pattern in intent_patterns.items():
                    score = fuzz.partial_ratio(text_lower, pattern)
                    # Also check token-based similarity
                    token_score = fuzz.token_set_ratio(text_lower, pattern)
                    final_score = max(score, token_score)
                    
                    if final_score > best_score:
                        best_score = final_score
                        best_match = intent
                
                # Use the best match if confidence is high enough
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
        
        # Special handling: if just a number and recent context was courses, treat as semester
        if not entities.get('semester') and not entities.get('department'):
            if re.match(r'^\d+$', user_input.strip()) and self.context:
                # Check if previous message was about courses
                for prev in reversed(self.context):
                    if prev.get('intent') == 'courses':
                        entities['semester'] = user_input.strip()
                        break
        
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
            timings = self.college_info.get('timings', 'Timings not available')
            return f"🕒 **College Timings**\n\n" \
                   f"📅 {timings}\n\n" \
                   f"💡 *Please arrive 10 minutes before class starts!*"
        
        elif intent_tag == 'departments':
            depts = self.college_info.get('departments', [])
            response = "📚 **Our Departments**\n\n"
            for i, dept in enumerate(depts, 1):
                response += f"{i}. {dept}\n"
            response += "\n💡 *Ask about any department for more details!*"
            return response
        
        elif intent_tag == 'facilities':
            facilities = self.college_info.get('facilities', [])
            response = "🏫 **Campus Facilities**\n\n"
            response += "✨ We offer the following facilities:\n\n"
            for i, facility in enumerate(facilities, 1):
                response += f"✓ {facility}\n"
            response += "\n💡 *Ask about specific facilities for detailed information!*"
            return response
        
        elif intent_tag == 'library':
            library = self.college_info.get('library', {})
            return f"📚 **Library Facilities**\n\n" \
                   f"🕒 **Timings:** {library.get('timings', 'N/A')}\n" \
                   f"📖 **Books Available:** {library.get('books', 'N/A')}\n" \
                   f"💻 **Digital Library:** {library.get('digital', 'Available')}\n" \
                   f"🪑 **Reading Room:** {library.get('reading_room', 'Available')}\n\n" \
                   f"💡 *Perfect place for your studies!*"
        
        elif intent_tag == 'hostel':
            hostel = self.college_info.get('hostel', {})
            return f"🏠 **Hostel Facilities**\n\n" \
                   f"✅ **Availability:** {hostel.get('available', 'Yes')}\n" \
                   f"👦 **Boys Hostel:** {hostel.get('boys', 'Available')}\n" \
                   f"👧 **Girls Hostel:** {hostel.get('girls', 'Available')}\n" \
                   f"💰 **Fees:** {hostel.get('fees', 'Contact hostel office')}\n" \
                   f"📞 **Contact:** {hostel.get('contact', 'N/A')}\n\n" \
                   f"💡 *Safe and comfortable accommodation for students!*"
        
        elif intent_tag == 'transport':
            transport = self.college_info.get('transport', {})
            return f"🚌 **Transport Facilities**\n\n" \
                   f"✅ **Bus Service:** {transport.get('available', 'Available')}\n" \
                   f"🗺️ **Routes:** {transport.get('routes', 'Multiple routes available')}\n" \
                   f"🕒 **Timings:** {transport.get('timings', 'Contact transport office')}\n" \
                   f"💰 **Fees:** {transport.get('fees', 'N/A')}\n\n" \
                   f"💡 *Convenient transportation from various locations!*"
        
        elif intent_tag == 'contact':
            contact = self.college_info.get('contact', {})
            address = self.college_info.get('address', 'N/A')
            return f"📞 **Contact Information**\n\n" \
                   f"📱 **Phone:** {contact.get('phone', 'N/A')}\n" \
                   f"📧 **Email:** {contact.get('email', 'N/A')}\n" \
                   f"📍 **Address:** {address}\n" \
                   f"🌐 **Website:** {self.college_info.get('website', 'N/A')}\n\n" \
                   f"💡 *Feel free to reach out anytime!*"
        
        elif intent_tag == 'courses':
            return self._handle_courses(entities)
        
        elif intent_tag == 'admission':
            admission = self.college_info.get('admission', {})
            return f"🎓 **Admissions Information**\n\n" \
                   f"✅ **Status:** {admission.get('status', 'Open')}\n" \
                   f"📅 **Last Date:** {admission.get('last_date', 'Check website')}\n" \
                   f"📋 **Eligibility:** {admission.get('eligibility', 'Check department wise')}\n" \
                   f"📧 **Email:** {admission.get('email', 'admissions@college.edu')}\n" \
                   f"📞 **Phone:** {admission.get('phone', 'Contact admission office')}\n\n" \
                   f"💡 *Apply now to secure your future!*"
        
        elif intent_tag == 'fees':
            return self._handle_fees(entities)
        
        elif intent_tag == 'scholarship':
            scholarship = self.college_info.get('scholarship', {})
            return f"💰 **Scholarship Opportunities**\n\n" \
                   f"🏆 **Merit Scholarship:** {scholarship.get('merit', 'Available')}\n" \
                   f"🤝 **Financial Aid:** {scholarship.get('financial_aid', 'Available for eligible students')}\n" \
                   f"🏛️ **Government Schemes:** {scholarship.get('government', 'Available')}\n" \
                   f"📞 **Contact:** {scholarship.get('contact', 'Scholarship cell')}\n\n" \
                   f"💡 *Don't let finances stop your dreams!*"
        
        elif intent_tag == 'placements':
            placements = self.college_info.get('placements', {})
            return f"💼 **Placement Statistics**\n\n" \
                   f"📊 **Placement Rate:** {placements.get('percentage', 'N/A')}\n" \
                   f"🎯 **Highest Package:** {placements.get('highest', 'N/A')}\n" \
                   f"📈 **Average Package:** {placements.get('average', 'N/A')}\n" \
                   f"🏢 **Top Recruiters:** {placements.get('companies', 'Multiple companies visit')}\n" \
                   f"📞 **Contact:** {placements.get('contact', 'Placement cell')}\n\n" \
                   f"💡 *Build your career with us!*"
        
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
            response = "⚽ **Sports Facilities**\n\n"
            response += "🏆 Available Sports:\n\n"
            for i, sport in enumerate(sports_list, 1):
                response += f"{i}. {sport}\n"
            response += "\n💡 *Stay fit and active with our sports facilities!*"
            return response
        
        elif intent_tag == 'clubs':
            clubs = self.college_info.get('clubs', {})
            clubs_list = clubs.get('available', [])
            response = "🎭 **Student Clubs**\n\n"
            response += "✨ Join our clubs:\n\n"
            for i, club in enumerate(clubs_list, 1):
                response += f"{i}. {club}\n"
            response += "\n💡 *Explore your interests and make new friends!*"
            return response
        
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
        
        # Get user input from context
        user_input_lower = ''
        if self.context:
            user_input_lower = self.context[-1].get('input', '').lower()
        
        # Department mapping for better matching
        dept_mapping = {
            'cse': 'Computer Science Engineering (CSE)',
            'computer science': 'Computer Science Engineering (CSE)',
            'cs': 'Computer Science Engineering (CSE)',
            'ece': 'Electronics & Communication (ECE)',
            'electronics': 'Electronics & Communication (ECE)',
            'mechanical': 'Mechanical Engineering',
            'mech': 'Mechanical Engineering',
            'civil': 'Civil Engineering',
            'eee': 'Electrical & Electronics (EEE)',
            'electrical': 'Electrical & Electronics (EEE)',
            'it': 'Information Technology (IT)',
            'information technology': 'Information Technology (IT)',
            'mca': 'MCA (Master of Computer Applications)',
            'mba': 'MBA (Master of Business Administration)'
        }
        
        # Check current input for department keywords first
        for keyword, full_name in dept_mapping.items():
            if keyword in user_input_lower:
                dept = full_name
                self.current_department = dept  # Remember this department
                break
        
        # If no dept found in current input, check context
        if not dept:
            # First check if we have a remembered department
            if self.current_department:
                dept = self.current_department
            # Otherwise look in previous messages
            elif self.context and len(self.context) > 1:
                for prev in reversed(self.context[:-1]):
                    if prev.get('intent') == 'courses':
                        prev_entities = prev.get('entities', {})
                        prev_dept = prev_entities.get('department')
                        if prev_dept:
                            dept = prev_dept
                            self.current_department = dept
                            break
                        # Also check the input text of previous message
                        prev_input = prev.get('input', '').lower()
                        for keyword, full_name in dept_mapping.items():
                            if keyword in prev_input:
                                dept = full_name
                                self.current_department = dept
                                break
                        if dept:
                            break
        
        if not dept:
            # List all departments with better formatting
            ug_programs = []
            pg_programs = []
            for name in self.courses.keys():
                if 'MCA' in name or 'MBA' in name:
                    pg_programs.append(name)
                else:
                    ug_programs.append(name)
            
            response = "📚 **Available Programs**\n\n"
            response += "**🎓 UG Programs (B.Tech):**\n"
            for i, prog in enumerate(ug_programs, 1):
                response += f"{i}. {prog}\n"
            response += "\n**🎓 PG Programs:**\n"
            for i, prog in enumerate(pg_programs, 1):
                response += f"{i}. {prog}\n"
            response += "\n💡 Ask about any specific program for details!"
            return response
        
        if dept not in self.courses:
            return f"Sorry, I don't have information about {dept}. " \
                   f"Please ask about available departments."
        
        dept_data = self.courses[dept]
        
        if sem and sem in dept_data.get('semesters', {}):
            subjects = dept_data['semesters'][sem]
            response = f"📖 **{dept}**\n\n"
            response += f"📚 **Semester {sem} Subjects:**\n\n"
            for i, subj in enumerate(subjects, 1):
                response += f"{i}. {subj}\n"
            response += f"\n💡 *Total: {len(subjects)} subjects*"
            return response
        else:
            sems = ', '.join(dept_data.get('semesters', {}).keys())
            fees = dept_data.get('fees', 'N/A')
            duration = dept_data.get('duration', '4 years')
            eligibility = dept_data.get('eligibility', '')
            specializations = dept_data.get('specializations', [])
            
            response = f"📖 **{dept}**\n\n"
            if duration:
                response += f"⏱️ Duration: {duration}\n"
            response += f"💰 Fees: {fees}\n"
            if eligibility:
                response += f"✅ Eligibility: {eligibility}\n"
            if specializations:
                response += f"🎯 Specializations: {', '.join(specializations)}\n"
            response += f"\n📋 Semesters: {sems}\n"
            response += "\n💡 Ask about specific semester for subject details!"
            return response
    
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
