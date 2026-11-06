"""Questions fictives, de style TOEIC, écrites pour le développement.

Entreprises, personnes et adresses sont inventées. Ce contenu ne provient pas
d'un vrai test TOEIC.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Passage, Question


def _q(
    category: str,
    difficulty: str,
    prompt: str,
    options: tuple[str, str, str, str],
    correct_choice: str,
    explanation: str,
) -> dict:
    return {
        "category": category,
        "difficulty": difficulty,
        "prompt": prompt,
        "options": dict(zip("ABCD", options)),
        "correct_choice": correct_choice,
        "explanation": explanation,
    }


PART_5 = [
    _q(
        "grammar", "easy",
        "All employees must ------- their identification badges at all times.",
        ("wearing", "wear", "worn", "wore"), "B",
        "Après le modal « must », on emploie la base verbale : « must wear ».",
    ),
    _q(
        "vocabulary", "easy",
        "The quarterly report was submitted ------- the deadline.",
        ("between", "among", "before", "during"), "C",
        "« Before the deadline » signifie « avant la date limite ». "
        "« Between » et « among » exigent plusieurs éléments.",
    ),
    _q(
        "grammar", "easy",
        "Ms. Tanaka has worked at Brightwell Logistics ------- 2015.",
        ("since", "for", "during", "at"), "A",
        "Avec le present perfect, « since » introduit un point de départ (2015) ; "
        "« for » introduirait une durée.",
    ),
    _q(
        "grammar", "easy",
        "The new software is ------- than the previous version.",
        ("reliable", "most reliable", "reliably", "more reliable"), "D",
        "« Than » appelle un comparatif ; pour un adjectif long : « more reliable ».",
    ),
    _q(
        "vocabulary", "easy",
        "Please ------- the attached form and return it by Friday.",
        ("arrive", "complete", "remain", "attend"), "B",
        "On remplit un formulaire : « complete a form ».",
    ),
    _q(
        "grammar", "easy",
        "Mr. Okafor rescheduled the meeting because ------- would be away on business.",
        ("him", "his", "he", "himself"), "C",
        "Il faut un pronom sujet devant le verbe « would be » : « he ».",
    ),
    _q(
        "grammar", "easy",
        "The marketing team reviewed the proposal ------- before presenting it to the client.",
        ("carefully", "careful", "care", "carefulness"), "A",
        "Un adverbe modifie le verbe « reviewed » : « carefully ».",
    ),
    _q(
        "grammar", "medium",
        "Neither the manager ------- her assistant was able to attend the conference.",
        ("or", "and", "but", "nor"), "D",
        "« Neither » forme une paire fixe avec « nor ».",
    ),
    _q(
        "grammar", "medium",
        "If the shipment ------- by Monday, we will contact the supplier.",
        ("did not arrive", "does not arrive", "had not arrived", "will not arrive"), "B",
        "Conditionnel de type 1 : « if » + présent simple, puis « will » dans la principale.",
    ),
    _q(
        "grammar", "medium",
        "The hotel offers free breakfast to all guests ------- stay exceeds three nights.",
        ("who", "which", "whose", "whom"), "C",
        "« Whose » exprime la possession : le séjour (« stay ») appartient aux clients.",
    ),
    _q(
        "vocabulary", "medium",
        "The contract must be signed by both parties ------- it can take effect.",
        ("before", "despite", "unless", "whereas"), "A",
        "La signature doit précéder l'entrée en vigueur : « before ». "
        "« Despite » ne peut pas introduire une proposition avec un verbe conjugué.",
    ),
    _q(
        "vocabulary", "easy",
        "Due to increased demand, the factory has ------- its production capacity.",
        ("resigned", "postponed", "retired", "expanded"), "D",
        "Une demande en hausse pousse à augmenter la capacité : « expand ».",
    ),
    _q(
        "vocabulary", "medium",
        "Applicants should have a ------- understanding of financial regulations.",
        ("punctual", "thorough", "vacant", "reluctant"), "B",
        "« A thorough understanding » signifie « une connaissance approfondie ».",
    ),
    _q(
        "vocabulary", "medium",
        "The board of directors will ------- the merger proposal at next week's meeting.",
        ("talk", "speak", "discuss", "comment"), "C",
        "Seul « discuss » est directement suivi d'un complément, sans préposition "
        "(« talk about », « comment on »).",
    ),
    _q(
        "grammar", "medium",
        "The renovation of the lobby is expected to be completed ------- the end of the month.",
        ("by", "since", "until", "from"), "A",
        "« By » indique une échéance. « Until » supposerait une action qui dure jusqu'à ce moment.",
    ),
    _q(
        "grammar", "medium",
        "Ms. Laurent's ------- to detail has earned her recognition across the department.",
        ("attentively", "attend", "attentive", "attention"), "D",
        "Après le possessif « Ms. Laurent's », il faut un nom : « attention to detail ».",
    ),
    _q(
        "grammar", "hard",
        "Had the team received the data earlier, they ------- the analysis on time.",
        ("will finish", "would have finished", "finished", "have finished"), "B",
        "Conditionnel de type 3 avec inversion : « Had + sujet + participe passé », "
        "puis « would have » + participe passé.",
    ),
    _q(
        "grammar", "hard",
        "The auditor's report was ------- clear that no further explanation was required.",
        ("such", "too", "so", "very"), "C",
        "Structure « so + adjectif + that ». « Such » s'emploie devant un groupe nominal.",
    ),
    _q(
        "vocabulary", "hard",
        "Additional chairs had to be ------- from the adjacent room for the seminar.",
        ("retrieved", "revoked", "reimbursed", "resolved"), "A",
        "« Retrieve » signifie « aller chercher, récupérer ». "
        "« Revoke » signifie « révoquer » et « reimburse » « rembourser ».",
    ),
    _q(
        "grammar", "hard",
        "Not until the audit was complete ------- the accountants leave the office.",
        ("had", "were", "have", "did"), "D",
        "« Not until » en tête de phrase entraîne une inversion ; "
        "la base verbale « leave » appelle l'auxiliaire « did ».",
    ),
    _q(
        "grammar", "easy",
        "The training session will begin ------- 9:00 A.M.",
        ("on", "in", "at", "to"), "C",
        "On emploie « at » devant une heure précise.",
    ),
    _q(
        "grammar", "easy",
        "Each of the new employees ------- a welcome package on the first day.",
        ("receive", "receiving", "are receiving", "receives"), "D",
        "« Each of » se construit avec un verbe au singulier : « receives ».",
    ),
    _q(
        "vocabulary", "easy",
        "Customers may ------- defective items within 30 days of purchase.",
        ("return", "hesitate", "recruit", "occur"), "A",
        "« Return an item » signifie « rapporter un article ».",
    ),
    _q(
        "grammar", "medium",
        "The budget proposal ------- by the finance committee last Tuesday.",
        ("approved", "was approved", "is approving", "has approving"), "B",
        "Le budget subit l'action et « last Tuesday » indique le passé : "
        "passif au prétérit, « was approved ».",
    ),
    _q(
        "vocabulary", "medium",
        "Because of its convenient location, the hotel is ------- with business travelers.",
        ("eager", "capable", "popular", "responsible"), "C",
        "« Popular with » signifie « apprécié de ».",
    ),
    _q(
        "grammar", "medium",
        "Mr. Silva is looking forward to ------- the new team next month.",
        ("meet", "met", "meets", "meeting"), "D",
        "Dans « look forward to », « to » est une préposition : elle est suivie de la forme en -ing.",
    ),
    _q(
        "vocabulary", "medium",
        "The warranty does not ------- damage caused by improper use.",
        ("attend", "cover", "apply", "depend"), "B",
        "Une garantie « couvre » un dommage : « cover ».",
    ),
    _q(
        "grammar", "hard",
        "Ms. Ito suggested that the report ------- to the directors before Friday.",
        ("be sent", "is sending", "sends", "sending"), "A",
        "Après « suggest that », on emploie le subjonctif, ici au passif : « be sent ».",
    ),
    _q(
        "vocabulary", "hard",
        "Profits rose sharply last year, largely ------- the success of the new product line.",
        ("in spite of", "owing to", "regardless of", "as though"), "B",
        "« Owing to » introduit une cause : le succès du produit explique la hausse des bénéfices.",
    ),
    _q(
        "grammar", "hard",
        "By the time the new director arrives in May, the team ------- the restructuring plan.",
        ("completes", "has completed", "was completing", "will have completed"), "D",
        "« By the time » + présent appelle le futur antérieur : « will have completed ».",
    ),
]

PART_6 = [
    {
        "title": "Email: Office relocation",
        "content": (
            "To: All staff\n"
            "From: Facilities Department\n"
            "Subject: Office relocation\n\n"
            "Dear colleagues,\n\n"
            "Northgate Consulting will move to its new headquarters on 14 March. Staff are "
            "asked to [1] their personal belongings in the boxes provided by 10 March. [2], "
            "the IT department will disconnect all computers on the evening of 12 March. The "
            "new building, [3] is located near Central Station, offers more meeting rooms "
            "and a larger cafeteria. [4]\n\n"
            "Regards,\n"
            "Facilities Department"
        ),
        "questions": [
            _q(
                "grammar", "easy",
                "Choose the word that best fits blank [1].",
                ("packing", "packed", "pack", "packs"), "C",
                "Après « asked to », on emploie la base verbale : « to pack ».",
            ),
            _q(
                "vocabulary", "medium",
                "Choose the expression that best fits blank [2].",
                ("Nevertheless", "In addition", "For example", "Otherwise"), "B",
                "La phrase ajoute une seconde information sur le déménagement : « In addition ».",
            ),
            _q(
                "grammar", "medium",
                "Choose the word that best fits blank [3].",
                ("which", "who", "where", "what"), "A",
                "Relatif sujet pour une chose (« the new building »), entre virgules : "
                "« which ». « Where » exigerait un sujet après lui.",
            ),
            _q(
                "comprehension", "hard",
                "Choose the sentence that best fits blank [4].",
                (
                    "Candidates must submit their résumés by Friday.",
                    "The restaurant has since closed permanently.",
                    "The invoice was paid in full last week.",
                    "Please contact our team if you have any questions about the move.",
                ),
                "D",
                "Seule cette phrase conclut logiquement un message sur le déménagement.",
            ),
        ],
    },
    {
        "title": "Notice: New opening hours",
        "content": (
            "Beginning on 3 June, Harbor Street Café will extend its opening hours. The café "
            "will now open at 6:30 A.M. on weekdays, [1] commuters can enjoy breakfast on "
            "their way to work. We have also [2] several vegetarian dishes to our lunch menu. "
            "To celebrate these changes, customers will receive a 10 percent discount on all "
            "drinks [3] the month of June. [4]"
        ),
        "questions": [
            _q(
                "grammar", "medium",
                "Choose the expression that best fits blank [1].",
                ("although", "because of", "unless", "so that"), "D",
                "« So that » introduit un but et est suivi d'une proposition complète.",
            ),
            _q(
                "grammar", "easy",
                "Choose the word that best fits blank [2].",
                ("added", "adding", "add", "adds"), "A",
                "Present perfect : « have » + participe passé, soit « have added ».",
            ),
            _q(
                "vocabulary", "medium",
                "Choose the word that best fits blank [3].",
                ("between", "throughout", "among", "beside"), "B",
                "« Throughout the month » signifie « pendant tout le mois ».",
            ),
            _q(
                "comprehension", "hard",
                "Choose the sentence that best fits blank [4].",
                (
                    "Our delivery trucks are being repaired.",
                    "We look forward to welcoming you soon.",
                    "The seminar has been canceled.",
                    "Please renew your passport in advance.",
                ),
                "B",
                "Seule cette phrase conclut logiquement une annonce adressée aux clients du café.",
            ),
        ],
    },
    {
        "title": "Letter: Subscription renewal",
        "content": (
            "Dear Ms. Alvarez,\n\n"
            "Thank you for renewing your subscription to Greenfield Business Review. Your next "
            "issue [1] on 5 September. As a valued subscriber, you now have [2] to our online "
            "archive. To activate this service, simply create an account on our website. [3], "
            "our customer service team is available on weekdays from 9 A.M. to 5 P.M. should "
            "you need help. [4]\n\n"
            "Sincerely,\n"
            "Subscriptions Department"
        ),
        "questions": [
            _q(
                "grammar", "easy",
                "Choose the words that best fit blank [1].",
                ("arrived", "arriving", "will arrive", "has arrived"), "C",
                "La date du 5 septembre est à venir : on emploie le futur, « will arrive ».",
            ),
            _q(
                "grammar", "medium",
                "Choose the word that best fits blank [2].",
                ("access", "accessible", "accessing", "accessed"), "A",
                "Après « have », il faut ici un nom : « have access to ».",
            ),
            _q(
                "vocabulary", "medium",
                "Choose the word or expression that best fits blank [3].",
                ("Instead", "Furthermore", "Even so", "In contrast"), "B",
                "La phrase ajoute un service supplémentaire : « Furthermore ».",
            ),
            _q(
                "comprehension", "hard",
                "Choose the sentence that best fits blank [4].",
                (
                    "The factory will close for repairs next week.",
                    "Please submit your expense reports by noon.",
                    "Our flights to Madrid depart twice daily.",
                    "We hope you continue to enjoy the magazine.",
                ),
                "D",
                "Seule cette phrase est liée à l'abonnement au magazine et conclut la lettre.",
            ),
        ],
    },
    {
        "title": "Article: New research center",
        "content": (
            "Technology company Ardent Systems announced on Monday that it [1] a new research "
            "center in Porto. The facility, which will open next spring, is expected to create "
            "about 200 jobs. Company spokesperson Ines Duarte said the city was chosen [2] its "
            "strong engineering universities. [3] the center opens, Ardent plans to recruit "
            "recent graduates directly. [4]"
        ),
        "questions": [
            _q(
                "grammar", "medium",
                "Choose the words that best fit blank [1].",
                ("would build", "building", "to build", "built"), "A",
                "Discours rapporté au passé d'un projet à venir : « announced that it would build ».",
            ),
            _q(
                "grammar", "medium",
                "Choose the expression that best fits blank [2].",
                ("although", "because of", "so that", "unless"), "B",
                "Devant le groupe nominal « its universities », la cause s'exprime avec « because of ».",
            ),
            _q(
                "grammar", "medium",
                "Choose the word that best fits blank [3].",
                ("Despite", "During", "Once", "Rather"), "C",
                "« Once » (« une fois que ») introduit une proposition avec un verbe conjugué.",
            ),
            _q(
                "comprehension", "hard",
                "Choose the sentence that best fits blank [4].",
                (
                    "The restaurant is closed on Mondays.",
                    "Ticket prices have been lowered.",
                    "The package was delivered to the wrong address.",
                    "Applications will be accepted starting in January.",
                ),
                "D",
                "La phrase précédente parle de recrutement : les candidatures en sont la suite logique.",
            ),
        ],
    },
]

PART_7 = [
    {
        "title": "Job advertisement: Solara Travel",
        "content": (
            "Solara Travel is seeking a Customer Service Supervisor for its Lyon office.\n\n"
            "Responsibilities include training new staff, handling escalated complaints and "
            "preparing weekly performance reports.\n\n"
            "Requirements: at least three years of experience in customer service and fluency "
            "in French and English. Knowledge of Spanish is an advantage. Occasional weekend "
            "work is required.\n\n"
            "To apply, send your résumé and two references to careers@solara-travel.example "
            "by 30 April."
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "What is the purpose of the text?",
                (
                    "To announce the opening of an office",
                    "To promote a travel package",
                    "To advertise a job opening",
                    "To respond to a customer complaint",
                ),
                "C",
                "Le texte décrit un poste, ses exigences et la façon de postuler.",
            ),
            _q(
                "comprehension", "medium",
                "What is NOT a requirement for the position?",
                (
                    "Knowledge of Spanish",
                    "Fluency in English",
                    "Customer service experience",
                    "Occasional weekend work",
                ),
                "A",
                "L'espagnol est seulement « an advantage » : un atout, pas une exigence.",
            ),
            _q(
                "comprehension", "easy",
                "What must applicants send?",
                (
                    "A cover letter and a diploma",
                    "A résumé and two references",
                    "A performance report",
                    "A language certificate",
                ),
                "B",
                "Le texte indique : « send your résumé and two references ».",
            ),
        ],
    },
    {
        "title": "Email: Delayed order",
        "content": (
            "Dear Mr. Novak,\n\n"
            "Thank you for your order (#48213) of 20 office chairs. Regrettably, the model you "
            "selected, the ErgoPlus 300, is temporarily out of stock because of a delay at our "
            "manufacturer. We now expect to ship your order by 18 May, about two weeks later "
            "than originally promised.\n\n"
            "Alternatively, we can send you the ErgoPlus 400, a higher-priced model, at no "
            "additional cost within three business days. Please let us know your preference "
            "by Friday.\n\n"
            "Sincerely,\n"
            "Priya Raman\n"
            "Customer Care, Fernhill Office Supplies"
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "Why did Ms. Raman write to Mr. Novak?",
                (
                    "To request payment for an invoice",
                    "To confirm a change of address",
                    "To introduce a new catalog",
                    "To inform him of a delivery delay",
                ),
                "D",
                "Elle annonce que la commande sera expédiée environ deux semaines plus tard.",
            ),
            _q(
                "comprehension", "medium",
                "What does Fernhill Office Supplies offer Mr. Novak?",
                (
                    "A more expensive model for the same price",
                    "A full refund of his order",
                    "A discount on his next order",
                    "Free chair assembly",
                ),
                "A",
                "L'ErgoPlus 400, plus cher, est proposé « at no additional cost ».",
            ),
            _q(
                "vocabulary", "medium",
                "The word \"selected\" in the first paragraph is closest in meaning to",
                ("delivered", "repaired", "chosen", "returned"), "C",
                "« The model you selected » signifie « le modèle que vous avez choisi ».",
            ),
            _q(
                "comprehension", "easy",
                "What is Mr. Novak asked to do by Friday?",
                (
                    "Return the chairs",
                    "State which option he prefers",
                    "Pay an additional fee",
                    "Call the manufacturer",
                ),
                "B",
                "Le texte indique : « Please let us know your preference by Friday ».",
            ),
        ],
    },
    {
        "title": "Memo: Business travel policy",
        "content": (
            "MEMO\n"
            "From: Daniel Cho, Vice President of Operations\n"
            "To: All department heads\n\n"
            "Effective 1 July, any business trip costing more than 1,000 euros will require "
            "written approval from the relevant department head. Employees are encouraged to "
            "hold meetings online whenever possible.\n\n"
            "We expect these measures to lower our travel expenses by 15 percent this year. "
            "The policy will be reviewed after six months, and your feedback will be welcome "
            "at that time."
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "What is the main topic of the memo?",
                (
                    "A change in business travel rules",
                    "A new online meeting platform",
                    "The appointment of a vice president",
                    "A reorganization of departments",
                ),
                "A",
                "Le mémo présente une nouvelle règle d'approbation des voyages d'affaires.",
            ),
            _q(
                "comprehension", "medium",
                "When will a trip need written approval?",
                (
                    "When it lasts more than six months",
                    "When it takes place in July",
                    "When it costs over 1,000 euros",
                    "When it involves a department head",
                ),
                "C",
                "Le texte indique : « any business trip costing more than 1,000 euros ».",
            ),
            _q(
                "comprehension", "hard",
                "What can be inferred about the company?",
                (
                    "It plans to close some departments.",
                    "It will stop all business travel.",
                    "It recently hired new department heads.",
                    "It wants to reduce its spending.",
                ),
                "D",
                "L'objectif de baisser les frais de déplacement de 15 % montre une volonté "
                "de réduire les dépenses. Les voyages restent toutefois autorisés.",
            ),
        ],
    },
    {
        "title": "Email: Trade expo registration",
        "content": (
            "Dear Ms. Bauer,\n\n"
            "This email confirms your registration for the Meridian Trade Expo, which will take "
            "place from 9 to 11 October at the Kestrel Convention Center. Your badge can be "
            "collected at the registration desk in Hall A from 8:00 A.M. each day. Please bring "
            "a photo ID.\n\n"
            "Your booth, number 214, will be available for setup on 8 October between 2:00 and "
            "6:00 P.M. Exhibitors who need extra electrical outlets should notify us by "
            "25 September.\n\n"
            "Best regards,\n"
            "Tomas Lind\n"
            "Exhibitor Services"
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "What is the purpose of the email?",
                (
                    "To cancel a booth reservation",
                    "To request a payment",
                    "To confirm a registration",
                    "To announce a change of venue",
                ),
                "C",
                "Le texte commence par : « This email confirms your registration ».",
            ),
            _q(
                "comprehension", "easy",
                "Where can Ms. Bauer get her badge?",
                ("At booth 214", "At the registration desk", "At her hotel", "By mail"), "B",
                "Le badge se retire « at the registration desk in Hall A ».",
            ),
            _q(
                "comprehension", "medium",
                "What is suggested about Ms. Bauer?",
                (
                    "She will display products at the event.",
                    "She works for the Kestrel Convention Center.",
                    "She organized the expo.",
                    "She will give a speech.",
                ),
                "A",
                "Elle dispose d'un stand à installer : elle participe donc comme exposante.",
            ),
            _q(
                "comprehension", "medium",
                "What should exhibitors do by 25 September if necessary?",
                (
                    "Set up their booths",
                    "Send a photo ID",
                    "Pay the registration fee",
                    "Request extra electrical outlets",
                ),
                "D",
                "Le texte précise : « need extra electrical outlets should notify us by 25 September ».",
            ),
        ],
    },
    {
        "title": "Notice: Elevator maintenance",
        "content": (
            "NOTICE TO TENANTS\n\n"
            "The elevators at Larkspur Tower will be out of service on Saturday, 12 May, from "
            "7:00 A.M. to 3:00 P.M. for annual inspection and maintenance. During this time, "
            "tenants should use the stairs located at the east and west ends of the building.\n\n"
            "Tenants expecting large deliveries that day should reschedule them. Anyone who "
            "requires assistance because of limited mobility should contact the building "
            "manager, Ms. Fofana, by Thursday, 10 May.\n\n"
            "We apologize for the inconvenience."
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "Why will the elevators be unavailable?",
                (
                    "A power outage is expected.",
                    "New elevators are being installed.",
                    "They will undergo regular maintenance.",
                    "The building is being sold.",
                ),
                "C",
                "L'arrêt est dû à « annual inspection and maintenance », donc à un entretien régulier.",
            ),
            _q(
                "comprehension", "easy",
                "What should tenants do about large deliveries on 12 May?",
                (
                    "Reschedule them",
                    "Bring them up the west stairs",
                    "Report them to Ms. Fofana",
                    "Leave them in the lobby",
                ),
                "A",
                "Le texte indique : « should reschedule them ».",
            ),
            _q(
                "comprehension", "medium",
                "Who is asked to contact Ms. Fofana?",
                (
                    "Workers repairing the elevators",
                    "People who have difficulty using stairs",
                    "Tenants who are moving out",
                    "Delivery drivers",
                ),
                "B",
                "« Limited mobility » désigne les personnes à mobilité réduite, gênées par les escaliers.",
            ),
            _q(
                "vocabulary", "medium",
                "The phrase \"out of service\" in the first paragraph is closest in meaning to",
                ("too expensive", "fully booked", "very busy", "not operating"), "D",
                "« Out of service » signifie « hors service », donc « not operating ».",
            ),
        ],
    },
    {
        "title": "Advertisement: The Hive Workspace",
        "content": (
            "The Hive Workspace: flexible offices in downtown Ashford\n\n"
            "Day Pass: 25 euros (shared desk, Wi-Fi, coffee)\n"
            "Monthly Membership: 290 euros (shared desk, 24-hour access, five hours of meeting "
            "room use)\n"
            "Private Office: from 650 euros per month (all membership benefits plus a locked "
            "office and mail handling)\n\n"
            "Sign up before 31 August and your first month of membership is half price. Free "
            "tours are offered every Tuesday at 11:00 A.M."
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "What is being advertised?",
                ("Work spaces for rent", "Office furniture", "A coffee shop", "Accounting services"),
                "A",
                "L'annonce présente des bureaux flexibles et leurs tarifs.",
            ),
            _q(
                "comprehension", "easy",
                "Which option includes mail handling?",
                ("A day pass", "A monthly membership", "A meeting room booking", "A private office"),
                "D",
                "« Mail handling » n'est mentionné que pour le « Private Office ».",
            ),
            _q(
                "comprehension", "medium",
                "What is true about the Monthly Membership?",
                (
                    "It includes a locked office.",
                    "It costs 25 euros.",
                    "It comes with 24-hour access.",
                    "It requires a one-year contract.",
                ),
                "C",
                "Le tarif mensuel inclut « 24-hour access ».",
            ),
            _q(
                "comprehension", "hard",
                "How much would a Monthly Membership cost for the first month if a customer "
                "signed up on 15 August?",
                ("25 euros", "145 euros", "290 euros", "325 euros"), "B",
                "Avant le 31 août, le premier mois est à moitié prix : 290 / 2 = 145 euros.",
            ),
        ],
    },
    {
        "title": "Article: Rosa's Bakery",
        "content": (
            "ELMSFORD - Rosa's Bakery, a fixture on Mill Road for nearly 30 years, will open a "
            "second location on Harbor Avenue next month. Owner Rosa Menendez started the "
            "business with just two employees; today she employs fourteen.\n\n"
            "\"Customers kept telling me the Mill Road shop was too small,\" Ms. Menendez said. "
            "The new shop will have seating for 40 people and will serve light lunches as well "
            "as baked goods.\n\n"
            "The Harbor Avenue site was previously occupied by a bookstore that moved to a "
            "larger building last year."
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "What is the article mainly about?",
                (
                    "The history of Mill Road",
                    "A new lunch menu at a bookstore",
                    "A local baking competition",
                    "A business opening a new location",
                ),
                "D",
                "L'article annonce l'ouverture d'une seconde boutique : « a second location ».",
            ),
            _q(
                "comprehension", "easy",
                "How many people does Ms. Menendez currently employ?",
                ("Two", "Fourteen", "Thirty", "Forty"), "B",
                "Le texte précise : « today she employs fourteen ».",
            ),
            _q(
                "comprehension", "medium",
                "Why is Ms. Menendez opening a second shop?",
                (
                    "The rent on Mill Road increased.",
                    "The Mill Road shop is closing.",
                    "Customers felt the original shop was too small.",
                    "A bookstore invited her to share its space.",
                ),
                "C",
                "Elle explique que ses clients trouvaient la boutique de Mill Road trop petite.",
            ),
            _q(
                "comprehension", "medium",
                "What is indicated about the bookstore?",
                (
                    "It relocated to a bigger space.",
                    "It went out of business.",
                    "It sells baked goods.",
                    "It belongs to Ms. Menendez.",
                ),
                "A",
                "La librairie a déménagé : « moved to a larger building last year ».",
            ),
        ],
    },
    {
        "title": "Invitation: Retirement dinner",
        "content": (
            "You are invited to a dinner honoring Dr. Helen Mbeki on her retirement after "
            "35 years with Castell Laboratories.\n\n"
            "Date: Friday, 22 November\n"
            "Time: 7:00 P.M. (reception at 6:30 P.M.)\n"
            "Place: The Orchard Room, Pemberton Hotel\n\n"
            "Dr. Mbeki joined the company as a junior researcher and has led its research "
            "division for the past twelve years. Please reply to Sam Whitlock at extension 318 "
            "by 8 November and indicate any dietary requirements. Colleagues wishing to "
            "contribute to a group gift may leave an envelope with Mr. Whitlock."
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "What is the reason for the event?",
                (
                    "To welcome a new director",
                    "To celebrate a product launch",
                    "To mark a colleague's retirement",
                    "To present research results",
                ),
                "C",
                "Le dîner est organisé pour « her retirement ».",
            ),
            _q(
                "comprehension", "easy",
                "What time does the reception start?",
                ("6:30 P.M.", "7:00 P.M.", "7:30 P.M.", "8:00 P.M."), "A",
                "Le texte précise : « reception at 6:30 P.M. ». Le dîner commence à 7:00 P.M.",
            ),
            _q(
                "comprehension", "medium",
                "What is stated about Dr. Mbeki?",
                (
                    "She founded Castell Laboratories.",
                    "She will move abroad.",
                    "She has worked at the company for twelve years.",
                    "She has led the research division.",
                ),
                "D",
                "Elle dirige la division de recherche depuis douze ans, mais travaille "
                "dans l'entreprise depuis 35 ans.",
            ),
            _q(
                "comprehension", "medium",
                "What should guests tell Mr. Whitlock when they reply?",
                (
                    "Their arrival time",
                    "Any food restrictions",
                    "Their hotel booking",
                    "Their gift preference",
                ),
                "B",
                "Il faut indiquer « any dietary requirements », c'est-à-dire les contraintes alimentaires.",
            ),
        ],
    },
    {
        "title": "Online chat: Client call",
        "content": (
            "Nadia Perrin [9:02 A.M.]: Hi Luc, the client from Vienna moved our call to "
            "2:00 P.M. Can you still join?\n"
            "Luc Moreau [9:04 A.M.]: I have the budget review until 2:30.\n"
            "Nadia Perrin [9:05 A.M.]: Could Emma take your place for the first half hour?\n"
            "Luc Moreau [9:06 A.M.]: Good idea. She knows the project well. I'll ask her and "
            "send her my notes.\n"
            "Nadia Perrin [9:07 A.M.]: Thanks. I'll book Room 4 and send the new invitation."
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "What has changed?",
                (
                    "The location of a client's office",
                    "The time of a call",
                    "The budget of a project",
                    "The members of a client's team",
                ),
                "B",
                "Le client a déplacé l'appel : « moved our call to 2:00 P.M. ».",
            ),
            _q(
                "comprehension", "easy",
                "Why can Mr. Moreau not attend the start of the call?",
                (
                    "He is traveling to Vienna.",
                    "He does not know the project.",
                    "He has another meeting.",
                    "He is preparing Room 4.",
                ),
                "C",
                "Il participe à la revue budgétaire jusqu'à 14 h 30.",
            ),
            _q(
                "comprehension", "hard",
                "At 9:06 A.M., what does Mr. Moreau mean when he writes, \"Good idea\"?",
                (
                    "He agrees that Emma should replace him at first.",
                    "He wants to cancel the call.",
                    "He prefers to use Room 4.",
                    "He would like to change the budget review.",
                ),
                "A",
                "Il répond à la proposition que Emma le remplace pendant la première demi-heure.",
            ),
            _q(
                "comprehension", "medium",
                "What will Ms. Perrin most likely do next?",
                (
                    "Send notes to Emma",
                    "Call the client in Vienna",
                    "Attend the budget review",
                    "Reserve a meeting room",
                ),
                "D",
                "Elle écrit : « I'll book Room 4 ». Ce sont les notes de Luc qui iront à Emma.",
            ),
        ],
    },
    {
        "title": "Product review: Aquila X2",
        "content": (
            "Rating: 3 out of 5 stars\n\n"
            "I bought the Aquila X2 coffee machine for our small office two months ago. It makes "
            "excellent coffee and is easy to clean, and the compact design fits well on our "
            "crowded counter. However, the water tank is small, so we have to refill it several "
            "times a day. I also contacted customer support about a missing filter, and it took "
            "them more than a week to respond. Once they did, the replacement arrived quickly "
            "and at no charge. Overall, it is a good machine for two or three people, but I "
            "would not recommend it for larger offices.\n\n"
            "J. Ortega"
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "What does the reviewer like about the machine?",
                (
                    "Its large water tank",
                    "The quality of its coffee",
                    "Its low price",
                    "The speed of its customer support",
                ),
                "B",
                "L'auteur écrit : « It makes excellent coffee ».",
            ),
            _q(
                "comprehension", "easy",
                "What problem does the reviewer mention about the machine?",
                (
                    "It is hard to clean.",
                    "It is too large for the counter.",
                    "It must be refilled often.",
                    "It makes too much noise.",
                ),
                "C",
                "Le réservoir étant petit, il faut le remplir « several times a day ».",
            ),
            _q(
                "comprehension", "medium",
                "What is said about customer support?",
                (
                    "It charged a fee for the filter.",
                    "It never replied.",
                    "It sent the wrong filter.",
                    "It took a long time to reply.",
                ),
                "D",
                "Le service a mis « more than a week to respond ». Le filtre est ensuite arrivé gratuitement.",
            ),
            _q(
                "comprehension", "medium",
                "Who would the reviewer most likely recommend the machine to?",
                ("A very small team", "A large office", "A busy restaurant", "A hotel"), "A",
                "L'auteur la conseille pour « two or three people », pas pour de grands bureaux.",
            ),
        ],
    },
    {
        "title": "Agenda: Negotiation workshop",
        "content": (
            "Effective Negotiation Workshop\n"
            "Vantage Training Center, 14 March\n\n"
            "9:00-9:30 Welcome and introductions (Karen Holt)\n"
            "9:30-11:00 Preparing for a negotiation (Karen Holt)\n"
            "11:00-11:15 Break\n"
            "11:15-12:30 Role-play exercises (Imran Aziz)\n"
            "12:30-1:30 Lunch (included in the fee)\n"
            "1:30-3:00 Handling difficult conversations (Imran Aziz)\n"
            "3:00-3:30 Review and certificates (Karen Holt)\n\n"
            "Participants should bring a recent example of a negotiation from their work."
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "What is the document for?",
                ("A job fair", "A training workshop", "A product launch", "A shareholder meeting"),
                "B",
                "Le titre indique : « Effective Negotiation Workshop ».",
            ),
            _q(
                "comprehension", "easy",
                "When do the role-play exercises begin?",
                ("9:30 A.M.", "12:30 P.M.", "11:15 A.M.", "1:30 P.M."), "C",
                "Le programme indique : « 11:15-12:30 Role-play exercises ».",
            ),
            _q(
                "comprehension", "medium",
                "What is indicated about lunch?",
                (
                    "It lasts two hours.",
                    "It is served at 11:00 A.M.",
                    "It is led by Karen Holt.",
                    "It is covered by the fee.",
                ),
                "D",
                "Le programme précise : « included in the fee ».",
            ),
            _q(
                "comprehension", "medium",
                "What should participants bring?",
                ("An example from their job", "A certificate", "A signed contract", "A laptop"),
                "A",
                "Le texte demande « a recent example of a negotiation from their work ».",
            ),
        ],
    },
    {
        "title": "Letter: Lease renewal",
        "content": (
            "Dear Mr. Haddad,\n\n"
            "The lease for your shop at 18 Canal Street expires on 30 June. If you wish to renew "
            "it, please return the enclosed agreement, signed, by 15 May.\n\n"
            "As discussed with your accountant, the monthly rent will increase by 3 percent from "
            "1 July. In exchange, the owner will repaint the exterior of the building and replace "
            "the front door at no cost to you this summer.\n\n"
            "If we do not hear from you by the above date, we will assume that you do not intend "
            "to stay and will begin advertising the property.\n\n"
            "Yours sincerely,\n"
            "Claire Dubois\n"
            "Dubois Property Management"
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "Why did Ms. Dubois write the letter?",
                (
                    "To offer a shop for sale",
                    "To explain the terms of a lease renewal",
                    "To ask for overdue rent",
                    "To complain about a repair",
                ),
                "B",
                "La lettre présente les conditions de renouvellement du bail.",
            ),
            _q(
                "comprehension", "easy",
                "What must Mr. Haddad return by 15 May to stay in the shop?",
                ("A signed agreement", "A rent payment", "An accountant's report", "A set of keys"),
                "A",
                "Le texte demande de renvoyer « the enclosed agreement, signed ».",
            ),
            _q(
                "comprehension", "medium",
                "What will the owner provide this summer?",
                (
                    "A lower rent",
                    "New shop furniture",
                    "Improvements to the building",
                    "Free advertising",
                ),
                "C",
                "Le propriétaire repeindra l'extérieur et remplacera la porte d'entrée.",
            ),
            _q(
                "comprehension", "hard",
                "What will happen if Mr. Haddad does not reply by the deadline?",
                (
                    "The rent will increase by a further 3 percent.",
                    "The lease will be renewed automatically.",
                    "His accountant will be contacted.",
                    "The shop will be offered to other tenants.",
                ),
                "D",
                "La société commencera « advertising the property » : le local sera proposé à d'autres.",
            ),
        ],
    },
    {
        "title": "Press release: Company merger",
        "content": (
            "FOR IMMEDIATE RELEASE\n\n"
            "Halden Foods and Brookvale Organics announced today that they have agreed to merge. "
            "The combined company, to be called Halden Brookvale, will have its headquarters in "
            "Copenhagen and about 3,200 employees.\n\n"
            "The merger, which is subject to regulatory approval, is expected to be finalized by "
            "the end of the year. Halden's current chief executive, Marta Olsen, will lead the "
            "new company, and Brookvale's founder, Peter Lang, will chair its board.\n\n"
            "Both companies stated that no factory closures are planned."
        ),
        "questions": [
            _q(
                "comprehension", "easy",
                "What is being announced?",
                (
                    "The sale of a factory",
                    "The retirement of a chief executive",
                    "The combining of two companies",
                    "A product recall",
                ),
                "C",
                "Le communiqué indique que les deux entreprises ont « agreed to merge ».",
            ),
            _q(
                "comprehension", "easy",
                "Who will run the new company?",
                ("Marta Olsen", "Peter Lang", "A government regulator", "A person yet to be named"),
                "A",
                "Marta Olsen « will lead the new company ». Peter Lang présidera le conseil.",
            ),
            _q(
                "vocabulary", "hard",
                "The phrase \"subject to\" in the second paragraph is closest in meaning to",
                ("opposed to", "dependent on", "famous for", "different from"), "B",
                "« Subject to approval » signifie « sous réserve d'approbation ».",
            ),
            _q(
                "comprehension", "medium",
                "What is stated about the factories?",
                (
                    "Several will move to Copenhagen.",
                    "They employ 3,200 people.",
                    "One of them will be sold.",
                    "None are scheduled to shut down.",
                ),
                "D",
                "Le texte précise : « no factory closures are planned ».",
            ),
        ],
    },
    {
        "title": "Employee handbook: Remote work",
        "content": (
            "Employee Handbook, Section 6: Remote Work\n\n"
            "Full-time employees who have completed their six-month probation period may work "
            "from home up to two days per week, with the approval of their supervisor. Remote "
            "work days must be recorded in the online calendar by noon on the preceding Friday.\n\n"
            "Employees are responsible for having a reliable internet connection. The company "
            "will provide a laptop but will not pay for home office furniture. All staff, "
            "including remote workers, are expected to attend the monthly department meeting "
            "in person."
        ),
        "questions": [
            _q(
                "comprehension", "medium",
                "Who is eligible to work from home?",
                (
                    "All newly hired staff",
                    "Part-time employees",
                    "Full-time staff who have finished their probation",
                    "Supervisors only",
                ),
                "C",
                "Le texte vise les « full-time employees who have completed their probation period ».",
            ),
            _q(
                "comprehension", "medium",
                "When must remote work days be recorded?",
                (
                    "By noon on the Friday before",
                    "At the monthly department meeting",
                    "At the end of each month",
                    "Six months in advance",
                ),
                "A",
                "Le texte indique : « by noon on the preceding Friday ».",
            ),
            _q(
                "comprehension", "easy",
                "What does the company provide to remote workers?",
                ("A desk", "A laptop", "An internet connection", "A chair"), "B",
                "L'entreprise fournit « a laptop », mais ni le mobilier ni la connexion.",
            ),
            _q(
                "comprehension", "medium",
                "What is required of all staff?",
                (
                    "Working from home two days per week",
                    "Buying their own laptops",
                    "Approving remote work requests",
                    "Attending a monthly meeting on site",
                ),
                "D",
                "Tous doivent assister en personne à la réunion mensuelle : « in person ».",
            ),
        ],
    },
]


def seed_if_empty(db: Session) -> None:
    """Remplit la base au premier démarrage ; ne touche pas à une base déjà remplie."""
    if db.scalar(select(func.count()).select_from(Question)):
        return

    db.add_all(Question(part=5, **question) for question in PART_5)
    for part, groups in ((6, PART_6), (7, PART_7)):
        for group in groups:
            passage = Passage(title=group["title"], content=group["content"])
            db.add_all(
                Question(part=part, passage=passage, **question)
                for question in group["questions"]
            )
    db.commit()
