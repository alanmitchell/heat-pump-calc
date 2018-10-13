"""Functions that create lists of Dash Input and State objects,
and convert the values from the components associated with those objects
into variables suitable for passing to energy models.
"""

input_info = [
    ('city', 'city_id'),
    ('elec_input',),
    ('utility', 'utility_id'),
    ('elec_rate_ez',),
    ('pce_ez', ),
    ('customer_chg_ez', ),
    ('blk1_min', ), 
    ('blk2_min', ), 
    ('blk3_min', ), 
    ('blk0_kwh', ),
    ('blk1_kwh', ),
    ('blk2_kwh', ),
    ('blk3_kwh', ),
    ('blk0_rate', ),
    ('blk1_rate', ),
    ('blk2_rate', ),
    ('blk3_rate', ),
    ('demand_chg_adv', ),
    ('pce_adv', ),
    ('customer_chg_adv', ),
]