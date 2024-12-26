(define (domain utc)
    (:requirements :typing)

    (:types road junction car use)

    (:predicates
        (togo ?c - car ?dest - junction)
        (connected ?junction1 - junction ?road - road ?junction2 - junction)
        (at ?car - car ?junction - junction)
        (next ?x ?y - use)
        (light ?r - road ?u - use)
        (medium ?r - road ?u - use)
        (heavy ?r - road ?u - use)
        (cap ?r - road ?u - use)
        (using ?r - road ?u - use)
    )

    (:functions
        (length-light ?road - road) ; time taking to drive to the road in light traffic
        (length-medium ?road - road) ; time taking to drive to the road in medium traffic
        (length-heavy ?road - road) ; time taking to drive to the road in heavy traffic
        (total-cost)
    )


    (:action DRIVE-TO-light
        :parameters (?c - car ?j1 - junction ?r - road ?j2 - junction ?d - junction ?u1 ?u2 - use)
            :precondition (and (togo ?c ?d)
                (using ?r ?u1)
                (next ?u1 ?u2)
                (light ?r ?u2)
                (at ?c ?j1)
                (connected ?j1 ?r ?j2)
            )

    :effect (and (not (using ?r ?u1))
            (using ?r ?u2)
            (not (at ?c ?j1))
            (at ?c ?j2)
            (increase (total-cost) (length-light ?r))
        )
    )


    (:action DRIVE-TO-medium
        :parameters (?c - car ?j1 - junction ?r - road ?j2 - junction ?d - junction ?u1 ?u2 - use)
            :precondition (and (togo ?c ?d)
                (using ?r ?u1)
                (next ?u1 ?u2)
                (medium ?r ?u2)
                (at ?c ?j1)
                (connected ?j1 ?r ?j2)
            )

    :effect (and (not (using ?r ?u1))
            (using ?r ?u2)
            (not (at ?c ?j1))
            (at ?c ?j2)
            (increase (total-cost) (length-medium ?r))
        )
    )


    (:action DRIVE-TO-heavy
        :parameters (?c - car ?j1 - junction ?r - road ?j2 - junction ?d - junction ?u1 ?u2 - use)
            :precondition (and (togo ?c ?d)
                (using ?r ?u1)
                (next ?u1 ?u2)
                (heavy ?r ?u2)
                (at ?c ?j1)
                (connected ?j1 ?r ?j2)
            )

    :effect (and (not (using ?r ?u1))
            (using ?r ?u2)
            (not (at ?c ?j1))
            (at ?c ?j2)
            (increase (total-cost) (length-heavy ?r))
        )
    )


    (:action DRIVE-TO-congested
        :parameters (?c - car ?j1 - junction ?r - road ?j2 - junction ?d - junction ?u1 - use)
            :precondition (and (togo ?c ?d)
                          (using ?r ?u1)
                          (cap ?r ?u1)
                          (at ?c ?j1)
                          (connected ?j1 ?r ?j2)
            )

    :effect (and (not (at ?c ?j1))
             (at ?c ?j2)
             (increase (total-cost) 100000)
         )
    )
)
