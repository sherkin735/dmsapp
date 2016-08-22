/**
 * Created by william on 18/08/16.
 */

function make_user_table() {
    var editor = new $.fn.dataTable.Editor({
        ajax: '/admin_user_table',
        table: '#users_table',
        idSrc: 'id',
        fields: [
            { label: 'Password Attempts', name: 'password_try_count'},
            { label: 'Username', name: 'username'  },
            { label: 'Name', name: 'name'  },
            { label: 'Access Level', name: 'access_level'  },
            { label: 'Password', name: 'password', type: 'password'  }
        ]
    });
    var user_table = $('#users_table').DataTable({
        ajax: '/admin_user_table',
        destroy: true,
        dom: 'Bfrtip',
        columns: [
            {
                data: null,
                defaultContent: '',
                className: 'select-checkbox',
                orderable: false
            },
            { data: 'password_try_count'},
            { data: 'username' },
            { data: 'name' },
            { data: 'access_level' },
            { data: 'password' }
        ],
        columnDefs: [
            {'title': 'Password Attempts', 'targets': 1},
            {'title': 'Username', 'targets': 2},
            {'title': 'Name', 'targets': 3},
            {'title': 'Access Level', 'targets': 4},
            {'title': 'Password', 'targets': 5}
        ],
        select: {
            style: 'os',
            selector: 'td:first-child'
        },
        buttons: [
            { extend: 'create', editor: editor },
            { extend: 'edit', editor: editor },
            { extend: 'remove', editor: editor }
        ]
    });

    user_table.buttons().container()
        .insertBefore('#example_filter');

    // Activate an inline edit on click of a table cell
    $('#users_table').on('click', 'tbody td:not(:first-child)', function (e) {
        editor.inline(this);
    });

    return user_table;
}

 function make_tag_table(){

    var tag_editor = new $.fn.dataTable.Editor( {
    ajax:  '/admin_tag_table',
    table: '#tags_table',
    idSrc:  'id',
    fields: [
        { label: 'TagID', name: 'id' },
        { label: 'Text', name: 'text'}
        ]
    } );

    var tag_table = $('#tags_table').DataTable( {
    ajax: '/admin_tag_table',
    destroy: true,
    dom: 'Bfrtip',
    columns: [
                    {
            data: null,
            defaultContent: '',
            className: 'select-checkbox',
            orderable: false
        },
        { data: 'id'},
        { data: 'text'}
        ],
    columnDefs: [
        {'title':'TagID', 'targets': 1},
        {'title':'Text', 'targets': 2}
        ],
    select: {
            style:    'os',
            selector: 'td:first-child'
        },
    buttons: [
        { extend: 'create', editor: tag_editor },
        { extend: 'edit',   editor: tag_editor },
        { extend: 'remove', editor: tag_editor }
    ]
    } );

    tag_table.buttons().container()
        .insertBefore( '#example_filter' );

    // Activate an inline edit on click of a table cell
    $('#tags_table').on( 'click', 'tbody td:not(:first-child)', function (e) {
        tag_editor.inline( this );
    } );

     return tag_table;

    }