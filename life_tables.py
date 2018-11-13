'''
CDC 2013 life tables
'''
import math
import constants


class LifeTables(object):
    '''
    Table[x] defines the probability of dying between ages [x] and [x+1]
    '''
    p_death = {
        constants.Sex.MALE: [
            0.006514, 0.000463, 0.000289, 0.000209, 0.000180, 0.000165,
            0.000148, 0.000132, 0.000115, 0.000099, 0.000090, 0.000097,
            0.000130, 0.000196, 0.000289, 0.000386, 0.000486, 0.000605,
            0.000740, 0.000880, 0.001024, 0.001152, 0.001245, 0.001296,
            0.001316, 0.001326, 0.001342, 0.001362, 0.001392, 0.001429,
            0.001470, 0.001509, 0.001543, 0.001571, 0.001601, 0.001640,
            0.001698, 0.001774, 0.001868, 0.001978, 0.002105, 0.002253,
            0.002425, 0.002631, 0.002875, 0.003143, 0.003443, 0.003798,
            0.004205, 0.004645, 0.005090, 0.005541, 0.006026, 0.006565,
            0.007158, 0.007794, 0.008451, 0.009124, 0.009803, 0.010500,
            0.011256, 0.012076, 0.012921, 0.013773, 0.014646, 0.015569,
            0.016603, 0.017800, 0.019228, 0.020906, 0.022826, 0.024998,
            0.027356, 0.029913, 0.032679, 0.035524, 0.039010, 0.043116,
            0.047647, 0.052626, 0.058301, 0.064637, 0.071412, 0.079031,
            0.087905, 0.098958, 0.110149, 0.122333, 0.135536, 0.149773,
            0.165040, 0.181318, 0.198565, 0.216721, 0.235701, 0.255399,
            0.275691, 0.296433, 0.317468, 0.338631, 1.000000
        ],

        constants.Sex.FEMALE: [
            0.005374, 0.000379, 0.000219, 0.000162, 0.000136, 0.000124,
            0.000110, 0.000100, 0.000094, 0.000091, 0.000093, 0.000100,
            0.000114, 0.000135, 0.000162, 0.000193, 0.000225, 0.000261,
            0.000299, 0.000338, 0.000377, 0.000415, 0.000447, 0.000471,
            0.000492, 0.000513, 0.000537, 0.000564, 0.000596, 0.000631,
            0.000670, 0.000711, 0.000752, 0.000794, 0.000841, 0.000897,
            0.000965, 0.001041, 0.001122, 0.001207, 0.001299, 0.001403,
            0.001523, 0.001663, 0.001827, 0.002004, 0.002197, 0.002421,
            0.002674, 0.002941, 0.003212, 0.003484, 0.003760, 0.004046,
            0.004351, 0.004680, 0.005028, 0.005391, 0.005766, 0.006166,
            0.006598, 0.007083, 0.007638, 0.008279, 0.009003, 0.009813,
            0.010703, 0.011675, 0.012753, 0.013958, 0.015325, 0.016892,
            0.018650, 0.020487, 0.022554, 0.024831, 0.027514, 0.030684,
            0.034250, 0.038265, 0.042554, 0.047066, 0.052561, 0.058864,
            0.066285, 0.074167, 0.083469, 0.093753, 0.105076, 0.117487,
            0.131021, 0.145700, 0.161528, 0.178486, 0.196532, 0.215597,
            0.235585, 0.256372, 0.277812, 0.299734, 1.000000
        ]
    }

    @staticmethod
    def adjusted_mortality(sex, age, adjustment):
        '''
        Adjust by increased risk of mortality
        '''
        prob_unadjusted = LifeTables.p_death[sex][age]
        rate_unadjusted = -1 * math.log(1 - prob_unadjusted)
        rate_adjusted = rate_unadjusted * adjustment
        prob_adjusted = 1 - math.exp(-rate_adjusted)
        return prob_adjusted
