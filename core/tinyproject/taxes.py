

class CanadaIncomeTaxCalculator:

    federal_bracket = {
        'first': (0, .15),
        'second': (55_867, .205),
        'third': (111_733, .26),
        'fourth': (173_205, .29),
        'fifth': (246_752, .33)
    }

    ns_bracket = {
        'first': (0, .0879),
        'second': (29_590, .1495),
        'third': (59_180, .1667),
        'fourth': (93_000, .175),
        'fifth': (150_000, .21)
    }
    
    def __values(self, data: dict) -> tuple:
        return data['second'][0] - data['first'][0], data['third'][0] - data['second'][0], data['fourth'][0] - data['third'][0], data['fifth'][0] - data['fourth'][0]


    def __rates(self, data):
        return data['first'][1], data['second'][1], data['third'][1], data['fourth'][1], data['fifth'][0]


    def __calculator(self, income, data):

        if income <= data['second'][0]:
            tax_payable = income * self.__rates(data)[0]

        elif income > data['second'][0] and income <= data['third'][0]:
            tax_payable = self.__rates(data)[0] *  self.__values(data)[0] + self.__rates(data)[1] * (income - self.__values(data)[0])

        elif income > data['third'][0] and income <= data['fourth'][0]:
            tax_payable = self.__rates(data)[0] * self.__values(data)[0] + \
                self.__rates(data)[1] * self.__values(data)[1] + \
                self.__rates(data)[2] * (income - self.__values(data)[0] - self.__values(data)[1]) 
            
        elif income > data['fourth'][0] and income <= data['fifth'][0]:
            tax_payable = self.__rates(data)[0] * self.__values(data)[0] + \
                self.__rates(data)[1] * self.__values(data)[1] + \
                self.__rates(data)[2] * self.__values(data)[2] + \
                self.__rates(data)[3] * (income - self.__values(data)[0] - self.__values(data)[1] - self.__values(data)[2]) 
        else:
            tax_payable = self.__rates(data)[0] * self.__values(data)[0] + \
                self.__rates(data)[1] * self.__values(data)[1] + \
                self.__rates(data)[2] * self.__values(data)[2] + \
                self.__rates(data)[3] * self.__values(data)[3] + \
                self.__rates(data)[4] * (
                    income - self.__values(data)[0] - self.__values(data)[1] - self.__values(data)[2] - self.__values(data)[3]
                ) 
        return tax_payable


    def federal_tax_calculator(self, income):
        data = self.federal_bracket
        return self.__calculator(income, data)

    def ns_tax_calculator(self, income):
        data = self.ns_bracket
        return self.__calculator(income, data)