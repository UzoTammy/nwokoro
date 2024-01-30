
dataset = {'1': 'One', '2': 'Two', '3': 'Three', '4': 'Four', '5': 'Five', '6': 'Six', '7': 'Seven', '8': 'Eight',
           '9': 'Nine', '10': 'Ten', '11': 'Eleven', '12': 'Twelve', '13': 'Thirteen', '14': 'Forteen', '15': 'Fifteen',
            '16': 'Sixteen', '17': 'Seventeen', '18': 'Eighteen', '19': 'Nineteen', '20': 'Twenty', '30': 'Thirty',
            '40': 'Forty', '50': 'Fifty', '60': 'Sixty', '70': 'Seventy', '80': 'Eighty', '90': 'Ninety'
        }

def figure_word(figure):

    figure = str(int(figure))

    if int(figure) >= 1e15:
        raise OverflowError("limit exceeded")
        
    if int(figure) <= 20:
        return dataset[figure]
    
    elif int(figure) > 20 and int(figure) < 100:
        # break into two
        if figure[1] == '0':
            result = dataset[figure]
        else:
            result = f"{dataset[figure[0]+'0']} {dataset[figure[1]]}"

    elif int(figure) >= 100 and int(figure) < 1000:
        # tear the number
        fn = figure_word(figure[0])
        ln = figure[1:]
        # zeros = dataset['00']
        if ln == 2*'0':
            result = f'{fn} Hundred'
        else:
            ln = str(int(ln))
            ln = figure_word(ln)
            result =  f'{fn} Hundred and {ln}' 
    
    elif int(figure) >= 1000 and int(figure) < 1e6:
        #tear down the number
        last_three_numbers = figure[-3:]
        first_numbers = figure[:-3]
        result = f'{last_three_numbers}, {first_numbers}'
        if last_three_numbers == 3*'0':
            result = f'{figure_word(first_numbers)} Thousand'
        else:
            fix = 'and ' if 2*'0' in last_three_numbers else ''
            fix = 'and ' if last_three_numbers[0] == '0' and last_three_numbers[1] != 0 else ''
            last_three_numbers = str(int(last_three_numbers))
            result = f'{figure_word(first_numbers)} Thousand, {fix}{figure_word(last_three_numbers)}'

    elif int(figure) >= 1e6 and int(figure) < 1e15:
        if int(figure) < 1e9:
            X = (6, 'Million')
        elif int(figure) >= 1e9 and int(figure) < 1e12:
            X = (9, 'Billion')
        elif int(figure) >= 1e12 and int(figure) < 1e15:
            X = (12, 'Trillion')

        # split the number into 2: the last digits and the rest
        last_digits = figure[-X[0]:]
        front_digits = figure[:-X[0]]
        
        if last_digits == X[0]*'0':
            result = f'{figure_word(front_digits)} {X[1]}'
        else:
            fix = 'and ' if int(last_digits) < 100 else ''
            digit = int(last_digits)
            result = f'{figure_word(front_digits)} {X[1]}, {fix}{figure_word(str(digit))}'
    return result
