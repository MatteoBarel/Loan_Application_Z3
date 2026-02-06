from z3 import *

class Applicant:
    def __init__(self, name, age, work, income, outstandingdebts,
                credit_score, requested, cosigner,
                typeloan, months, blacklisted):
        
        self.name = name
        self.age = age
        self.work = work
        self.income = income
        self.outstandingdebts = outstandingdebts
        self.credit_score = credit_score
        self.requested = requested
        self.cosigner = cosigner
        self.typeloan = typeloan
        self.months = months
        self.blacklisted = blacklisted



def loan_application(applicant):

    solver = Solver()
    approved = Bool("approved")

    rate = Real("rate")
    monthly_payment = Real("monthly_payment")
    
    age = RealVal(applicant.age)
    income = RealVal(applicant.income)
    score = applicant.credit_score
    months = applicant.months
    cosigner = BoolVal(applicant.cosigner)


    #implicazioni per l'età

    solver.add(Implies(age >= 75, Not(approved)))
    solver.add(Implies(And(age <= 25, Not(cosigner)), Not(approved)))


    #definiamo i tipi di lavoro, ogni richiedente può avere solo un tipo di lavoro

    is_permanent = Bool('is_permanent')
    is_temporary = Bool('is_temporary')
    is_unemployed = Bool('is_unemployed')

    solver.add(Or(is_permanent, is_temporary, is_unemployed))
    solver.add(Or(Not(is_permanent), Not(is_temporary)))
    solver.add(Or(Not(is_permanent), Not(is_unemployed)))
    solver.add(Or(Not(is_temporary), Not(is_unemployed)))

    solver.add(is_permanent == (applicant.work == 'permanent'))
    solver.add(is_temporary == (applicant.work == 'temporary'))
    solver.add(is_unemployed == (applicant.work == 'unemployed'))

    solver.add(Implies(Xor(is_unemployed,is_temporary), cosigner))


    #definiamo i tipi di prestito richiesto (al più uno per richiedente) e le condizioni

    is_personal = Bool('is_personal')
    is_car = Bool('is_car')
    is_house = Bool('is_house')

    solver.add(Or(is_personal, is_car, is_house))
    solver.add(Or(Not(is_personal), Not(is_car)))
    solver.add(Or(Not(is_personal), Not(is_house)))
    solver.add(Or(Not(is_car), Not(is_house)))

    solver.add(is_personal == (applicant.typeloan == 'personal'))
    solver.add(is_car == (applicant.typeloan == 'car'))
    solver.add(is_house == (applicant.typeloan == 'house'))

    solver.add(Implies(is_car, applicant.requested <= 50000))
    solver.add(Implies(is_house, applicant.requested >= 30000))

    solver.add(Implies(is_car, applicant.outstandingdebts <= 5000))


    #definiamo il tasso base secondo lo score (è giovane viene "penalizzato")

    base_rate = Real("base_rate")
    solver.add(Implies(age <= 35, base_rate == (1000 - score) * 0.017 + 0.5*Sqrt(35-age)))
    solver.add(Implies(age > 35, base_rate == (1000 - score) * 0.017))

    #abbassiamo il tasso per il mutuo

    type_adj = Real("type_adj")
    solver.add(
        type_adj ==
        If(is_house, -2.0,0)
    )


    #aggiustiamo il tasso in base alle entrate

    income_adj = Real("income_adj")
    solver.add(
        income_adj ==
        If(income >= 4500, -0.1,
        If(income >= 3500,  0.0,
        If(income >= 2500,  0.1,
        If(income >= 2000,  0.2,
                                0.3))))
    )
    

    #aggiustiamo il tasso in base alla richiesta

    dti_adj = Real("dti_adj")
    solver.add(
        dti_adj ==
        If(applicant.requested <= 10000, -0.1,
        If(applicant.requested <= 25000,  0.0,
        If(applicant.requested <= 40000,  0.1,
                                            0.2)))
    )
    

    #sommiamo le caratteristiche

    solver.add(rate == If(approved, base_rate + type_adj + income_adj + dti_adj, 0))


    #rata mensile

    solver.add(
        monthly_payment == If(approved, 
                    applicant.requested / months + rate/100 * applicant.requested / months, 
                    0)
    )
    

    mp = applicant.requested / months + rate/100 * applicant.requested / months
    
    solver.add(
        approved == 
        If(is_house, 
            mp <= 0.5 * income,  
            mp <= 0.2 * income)
        )


    solver.add(Implies(applicant.blacklisted, Not(approved)))

    solver.add(approved)

    if solver.check() == sat:
        model = solver.model()

        print("APPROVATO")
        
        print(f"{applicant.name}")
        
        r = model.eval(rate)
        r_val = float(r.as_decimal(10).replace("?", ""))
            
        print(f"Tasso: {r_val:.2f}%")
        print(f"Reddito: €{applicant.income}")
        print(f"Importo: €{applicant.requested}")
        print(f"Credit score: {applicant.credit_score}")
            
        mp = model.eval(monthly_payment)
        mp_val = float(mp.as_decimal(10).replace("?", ""))
            
        print(f"Rata mensile ({months} mesi): €{mp_val:.2f}")
        interests = mp_val *months - applicant.requested
        print(f"Interessi totali: €{interests:.2f}")

    else:
        print('\n')
        print("RIFIUTATO")
        print(f"{applicant.name}")
        if applicant.blacklisted:
            print("Motivo: Cliente nella blacklist")
        elif applicant.age > 75:
            print("Motivo: Età non conforme")
        elif applicant.age <= 25 and applicant.cosigner == False:
            print("Motivo: mancanza di un co-firmatario")
        elif applicant.credit_score < 100:
            print("Motivo: Credit score insufficiente")
        elif applicant.income < 1000:
            print("Motivo: Reddito insufficiente")
        else:
            print("Motivo: Tasso o sostenibilità non rispettati")


maria = Applicant(name="Maria",
                    age =54,
                    work = 'permanent',
                    income = 3400,
                    outstandingdebts = 0,
                    credit_score = 650,
                    requested = 40000,
                    cosigner = True,
                    typeloan = 'car',
                    months = 120,
                    blacklisted = False)

loan_application(maria)